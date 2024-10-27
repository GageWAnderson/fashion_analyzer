import asyncio
import logging
from functools import partial
from typing import AsyncGenerator, Any, Union

from pydantic import BaseModel, ConfigDict
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from common.utils.llm import get_llm_from_config

from backend.app.config.config import BackendConfig, backend_config
from backend.app.utils.streaming import AsyncStreamingCallbackHandler, StreamingData
from backend.app.schemas.agent_state import AgentState
from backend.app.schemas.subgraph import Subgraph, SubgraphSelectionResponse
from backend.app.graphs.rag import RagGraph
from backend.app.graphs.clothing_search import ClothingSearchGraph
from backend.app.schemas.should_continue import ShouldContinueResponse
from backend.app.nodes.end import EndNode
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
    stream_handler: AsyncStreamingCallbackHandler
    queue: asyncio.Queue
    stop_event: asyncio.Event
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    async def from_config(
        cls,
        config: BackendConfig,
    ) -> "ChatGraph":
        queue = asyncio.Queue()
        stop_event = asyncio.Event()
        stream_handler = AsyncStreamingCallbackHandler(
            streaming_function=partial(cls._streaming_function, queue)
        )
        graph = StateGraph(AgentState)
        vector_store = await PgVectorStore.from_config(config)

        # TODO: Consider abstracting this into a function that takes a config
        subgraphs: list[Subgraph] = [
            RagGraph.from_config(config, vector_store, stream_handler),
            ClothingSearchGraph.from_config(config, stream_handler),
        ]

        # TODO: Refactor chat graph to have the available tools as sub-graphs
        graph.add_node(EndNode.get_name(), EndNode.from_handler(stream_handler))
        graph.add_edge(EndNode.get_name(), END)
        for subgraph in subgraphs:
            graph.add_node(subgraph.get_name(), subgraph)
            graph.add_edge(subgraph.get_name(), EndNode.get_name())

        graph.add_conditional_edges(
            START,
            partial(
                ChatGraph.select_subgraph,
                llm=get_llm_from_config(config, config.tool_call_llm),
                subgraphs=subgraphs,
            ),
            [subgraph.get_name() for subgraph in subgraphs],
        )

        return cls(
            graph=graph.compile(),
            queue=queue,
            stop_event=stop_event,
            stream_handler=stream_handler,
        )

    async def ainvoke(self, *args, **kwargs) -> Union[dict[str, Any], Any]:
        """
        Wrapper function to invoke the graph with the streaming callback handler.
        """
        result = None
        await self.stream_handler.on_llm_start(serialized={}, prompts=[], **kwargs)
        try:
            result = await self.graph.ainvoke(*args, **kwargs)
        except Exception:
            error_message = """I'm sorry, but there was an issue while processing your request.
                Please rephrase and try again."""
            await self.stream_handler.on_text(text=error_message, **kwargs)
            logger.exception("There was an exception in the agent graph")
        finally:
            await self.stream_handler.on_llm_end()
            self.stop_event.set()  # TODO: Is this the best way to stop the graph?

        return result

    async def process_queue(self) -> AsyncGenerator[str, None]:
        while not self.stop_event.is_set():
            try:
                item = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                yield item
                self.queue.task_done()
            except asyncio.TimeoutError:
                continue

    @staticmethod
    async def select_subgraph(
        llm: BaseLanguageModel,
        subgraphs: list[Subgraph],
        state: AgentState,
    ) -> str:
        """
        Selects the appropriate action plan for the user's question.
        """
        prompt = PromptTemplate(
            input_variables=["user_question", "subgraph_descriptions"],
            template=backend_config.select_action_plan_prompt,
        ).format(
            user_question=state["user_question"],
            subgraph_descriptions="\n".join(
                [subgraph.get_description() for subgraph in subgraphs]
            ),
        )
        # TODO: Consider using .with_structured_output() to add structured output to subgraph selection
        subgraph_choice_llm = llm.with_structured_output(SubgraphSelectionResponse)
        raw_selected_subgraph = await subgraph_choice_llm.ainvoke(
            [SystemMessage(content=prompt)]
        )
        return SubgraphSelectionResponse.model_validate(
            raw_selected_subgraph
        ).subgraph_name

    @staticmethod
    async def _streaming_function(queue: asyncio.Queue, data: StreamingData):
        await queue.put(data)

    @staticmethod
    async def _should_continue(state: AgentState) -> str:
        continue_prompt = PromptTemplate(
            input_variables=["original_question", "last_message"],
            template=backend_config.should_continue_prompt,
        )
        messages = state.get("messages", [])
        if not messages:
            return "continue"

        original_question = next(
            (
                msg.content
                for msg in reversed(messages)
                if isinstance(msg, HumanMessage)
            ),
            None,
        )
        if original_question is None:
            return "continue"

        last_message = messages[-1]

        if isinstance(last_message, ToolMessage) and last_message.status == "error":
            return "end"

        prompt = continue_prompt.format(
            original_question=original_question, last_message=last_message.content
        )

        llm = get_llm_from_config(
            backend_config, backend_config.tool_call_llm
        ).with_structured_output(ShouldContinueResponse)

        try:
            response = await llm.ainvoke([SystemMessage(content=prompt)])
            return "continue" if response.should_continue else "end"
        except Exception:
            logger.exception("Error parsing should continue response")
            logger.warning(
                "Should continue response is invalid, possibly ending chat prematurely"
            )
            return "end"
