import asyncio
import logging
from functools import partial
from typing import AsyncGenerator, Any, Union

from pydantic import BaseModel, ConfigDict
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langchain_core.prompts import PromptTemplate
from common.utils.llm import get_llm_from_config

from backend.app.config.config import BackendConfig, backend_config
from backend.app.utils.streaming import AsyncStreamingCallbackHandler, StreamingData
from backend.app.tools.qa import QaTool
from backend.app.tools.rag import RagTool
from backend.app.tools.search import SearchTool
from backend.app.schemas.agent_state import AgentState
from backend.app.nodes.agent import AgentNode
from backend.app.nodes.action import ActionNode
from backend.app.schemas.should_continue import ShouldContinueResponse

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
    def from_config(
        cls,
        config: BackendConfig,
    ) -> "ChatGraph":
        queue = asyncio.Queue()
        stop_event = asyncio.Event()
        stream_handler = AsyncStreamingCallbackHandler(
            streaming_function=partial(cls._streaming_function, queue)
        )
        graph = StateGraph(AgentState)

        # TODO: Consider abstracting this into a function that takes a config
        tools = [
            QaTool(stream_handler=stream_handler),
            RagTool(stream_handler=stream_handler),
            SearchTool(stream_handler=stream_handler),
        ]

        graph.add_node(
            "agent",
            AgentNode(get_llm_from_config(config, config.tool_call_llm), tools),
        )
        graph.add_node("action", ActionNode(tools, stream_handler))

        graph.add_edge(START, "agent")
        graph.add_edge("agent", "action")
        graph.add_conditional_edges(
            "action", cls._should_continue, path_map={"continue": "agent", "end": END}
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

        # llm = get_llm_from_config(
        #     backend_config, backend_config.tool_call_llm
        # ).bind_tools([ShouldContinueResponse])

        try:
            response = await llm.ainvoke([SystemMessage(content=prompt)])
            logger.debug(f"Should continue response: {response}")
            if not response.tool_calls[0]["args"]:
                logger.warning(
                    "Should continue response is invalid, possibly ending chat prematurely"
                )
                return "end"
            response = ShouldContinueResponse(**response.tool_calls[0]["args"])
            return "continue" if response.should_continue else "end"
        except Exception:
            logger.exception("Error parsing should continue response")
            return "end"
