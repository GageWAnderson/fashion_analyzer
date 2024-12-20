import re
import asyncio
import logging
from functools import partial
from typing import AsyncGenerator, Any, Union, Optional

from pydantic import BaseModel, ConfigDict
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from common.utils.llm import get_llm_from_config

from backend.app.config.config import BackendConfig, backend_config
from backend.app.utils.streaming import AsyncStreamingCallbackHandler, StreamingData
from backend.app.schemas.agent_state import AgentState
from backend.app.schemas.subgraph import Subgraph
from backend.app.graphs.rag import RagGraph
from backend.app.graphs.clothing_search import ClothingSearchGraph
from backend.app.nodes.end import EndNode
from backend.app.nodes.subgraph_start import SubgraphStartNode
from common.db.vector_store import PgVectorStore

logger = logging.getLogger(__name__)


class ChatGraph(BaseModel):
    """
    This graph implements a simle ReACT style agent.
    The tool calling LLM first selects the appropriate tool to call given the user's question.
    Then, the appropriate tool is called and the results are streamed back to the user.
    Note that the tools called can be graphs themselves, allowing for complex workflows.

    This graph handles the streaming of the agent's response to the user through the callback handler.
    """

    graph: CompiledStateGraph
    stream_handler: Optional[AsyncStreamingCallbackHandler] = None
    queue: Optional[asyncio.Queue] = None
    stop_event: Optional[asyncio.Event] = None
    subgraphs: list[Subgraph]
    llm: BaseLanguageModel
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    async def from_config(
        cls,
        config: BackendConfig,
        test_mode: bool = False,
    ) -> "ChatGraph":
        """
        Creates a ChatGraph from a BackendConfig.
        Setting test_mode to True will create a ChatGraph without a stream handler,
        allowing for testing without streaming.
        """
        queue = asyncio.Queue(maxsize=backend_config.max_queue_size)
        stop_event = asyncio.Event()
        stream_handler = (
            AsyncStreamingCallbackHandler(
                streaming_function=partial(cls._streaming_function, queue)
            )
            if not test_mode
            else None
        )
        graph = StateGraph(AgentState)
        vector_store = await PgVectorStore.from_config(config)

        subgraphs = cls._get_subgraphs_from_config(config, vector_store, stream_handler)

        end_node = EndNode.from_handler(stream_handler)
        graph.add_node(end_node.name, end_node)
        graph.add_edge(end_node.name, END)
        for subgraph in subgraphs:
            graph.add_node(
                ChatGraph.get_subgraph_start_node_name(subgraph.name),
                SubgraphStartNode.from_handler(subgraph.name, stream_handler),
            )
            graph.add_node(subgraph.name, subgraph.graph)
            graph.add_edge(
                ChatGraph.get_subgraph_start_node_name(subgraph.name),
                subgraph.name,
            )
            graph.add_edge(subgraph.name, end_node.name)

        graph.add_conditional_edges(
            START,
            partial(
                ChatGraph.select_subgraph,
                get_llm_from_config(config, config.fast_llm),
                subgraphs,
            ),
            [
                ChatGraph.get_subgraph_start_node_name(subgraph.name)
                for subgraph in subgraphs
            ],
        )

        return cls(
            graph=graph.compile(),
            queue=queue,
            stop_event=stop_event,
            stream_handler=stream_handler,
            subgraphs=subgraphs,
            llm=get_llm_from_config(config, config.fast_llm),
        )

    async def ainvoke(self, *args, **kwargs) -> Union[dict[str, Any], Any]:
        """
        Wrapper function to invoke the graph with the streaming callback handler.
        """
        result = None
        if self.stream_handler:
            await self.stream_handler.on_llm_start(serialized={}, prompts=[], **kwargs)
        try:
            # Log queue size periodically
            if self.queue and self.queue.qsize() > backend_config.max_queue_size * 0.5:
                logger.warning(f"Queue size is large: {self.queue.qsize()}")

            result = await self.graph.ainvoke(*args, **kwargs)
        except Exception:
            error_message = """\nI'm sorry, but there was an issue while processing your request.
                Please rephrase and try again."""
            if self.stream_handler:
                await self.stream_handler.on_text(text=error_message, **kwargs)
            logger.exception("There was an exception in the agent graph")
        finally:
            if self.stop_event:
                self.stop_event.set()

        return result

    async def process_queue(self) -> AsyncGenerator[str, None]:
        if not self.queue or not self.stop_event:
            return

        while not self.stop_event.is_set():
            try:
                # Check if queue is getting too full
                if self.queue.qsize() > 80:  # 80% of maxsize
                    logger.warning("Queue is backing up, applying backpressure")
                    await asyncio.sleep(0.1)
                    continue

                item = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                yield item
                self.queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing queue item: {e}")
                continue

    @staticmethod
    def _get_subgraphs_from_config(
        config: BackendConfig,
        vector_store: PgVectorStore,
        stream_handler: Optional[AsyncStreamingCallbackHandler],
    ) -> list[Subgraph]:
        # TODO: Consider abstracting this into a function that takes a config
        # TODO: Add a missing_tool to filter out irrelevant requests
        return [
            RagGraph.from_config(config, vector_store, stream_handler),
            ClothingSearchGraph.from_config(config, stream_handler),
        ]

    @staticmethod
    async def select_subgraph(
        llm: BaseLanguageModel,
        subgraphs: list[Subgraph],
        state: AgentState,
    ) -> str:
        """
        Selects the appropriate subgraph to answer the user's question.
        The agent can call one subgraph per user question before returning.
        """
        prompt = PromptTemplate(
            input_variables=["user_question", "subgraph_descriptions"],
            template=backend_config.select_action_plan_prompt,
        ).format(
            user_question=state["user_question"],
            subgraph_descriptions="\n".join(
                [
                    f"Name: {subgraph.name}:\nDescription: {subgraph.description}\n"
                    for subgraph in subgraphs
                ]
            ),
        )
        # TODO: Consider using .with_structured_output() to add structured output to subgraph selection
        # subgraph_choice_llm = llm.with_structured_output(SubgraphSelectionResponse)
        # return SubgraphSelectionResponse.model_validate(
        #     raw_selected_subgraph
        # ).subgraph_name

        # TODO: Consider using structured output if given a more powerful LLM
        # TODO: Build a switch on the LLM type that changes parsing mode depending on model power
        # BUG: Ollama silently fails if given a SystemMessage instead of human, ai message
        raw_res = await llm.ainvoke(input=[HumanMessage(content=prompt)])
        raw_selected_subgraph = AIMessage.model_validate(raw_res).content
        logger.info(f"Raw subgraph response: {raw_selected_subgraph}")
        selected_subgraph = ChatGraph.parse_subgraph_response(
            raw_selected_subgraph, [subgraph.name for subgraph in subgraphs]
        )
        logger.info(f"Selected subgraph: {selected_subgraph}")
        return ChatGraph.get_subgraph_start_node_name(selected_subgraph)

    @staticmethod
    def parse_subgraph_response(
        raw_selected_subgraph: str,
        subgraph_names: list[str],
    ) -> str:
        # Create regex pattern that matches any of the subgraph names
        pattern = "|".join(map(re.escape, subgraph_names))

        # Search for first match of any subgraph name
        match = re.search(pattern, raw_selected_subgraph)

        if not match:
            raise ValueError(
                f"Could not find any valid subgraph names in response. "
                f"Expected one of: {', '.join(subgraph_names)}"
            )

        return match.group(0)

    @staticmethod
    async def _streaming_function(queue: asyncio.Queue, data: StreamingData):
        await queue.put(data)

    @staticmethod
    def get_subgraph_start_node_name(subgraph_name: str) -> str:
        return f"start_{subgraph_name}"
