import asyncio
import logging
from functools import partial
from typing import Annotated, Sequence, TypedDict
import operator
from typing import AsyncGenerator, Any, Union

from pydantic import BaseModel, ConfigDict
from langchain_core.messages import ToolMessage, HumanMessage
from langchain_core.language_models import BaseLanguageModel
from langgraph.graph import StateGraph, START, END
from langchain.schema import BaseMessage, AIMessage
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langgraph.graph.state import CompiledStateGraph
from langchain_core.tools import BaseTool
from langchain_core.prompts import PromptTemplate
from common.utils.llm import get_llm_from_config

from backend.app.config.config import BackendConfig, backend_config
from backend.app.utils.streaming import AsyncStreamingCallbackHandler, StreamingData
from backend.app.tools.qa import QaTool
from backend.app.tools.rag import RagTool
from backend.app.tools.search import SearchTool
from backend.app.schemas.exceptions import UserFriendlyException

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


async def should_continue(llm: BaseLanguageModel, state: AgentState) -> str:
    continue_prompt = PromptTemplate(
        input_variables=["original_question", "last_message"],
        template=backend_config.should_continue_prompt,
    )
    messages = state.get("messages", [])
    if not messages:
        return "continue"

    original_question = next(
        (msg.content for msg in reversed(messages) if isinstance(msg, HumanMessage)),
        None,
    )
    if original_question is None:
        return "continue"

    last_message = messages[-1]

    prompt = continue_prompt.format(
        original_question=original_question, last_message=last_message.content
    )

    # TODO: Consider more robust output parsing with a tool calling LLM for structure
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return "end" if "yes" in response.content.strip().lower() else "continue"


# async def should_continue(
#     stream_handler: AsyncStreamingCallbackHandler, state: AgentState
# ) -> str:
#     if state["messages"][-1].tool_calls:
#         return "continue"
#     else:
#         return "end"


async def agent(
    model: BaseLanguageModel,
    stream_handler: AsyncStreamingCallbackHandler,
    tools: Sequence[BaseTool],
    state: AgentState,
) -> AgentState:
    """
    Selects the tool to call given the messages in the conversation.
    Returns the JSON response with the tool call info to be executed by the action node.
    """
    # Extract the last user message
    last_user_message = next(
        (msg for msg in reversed(state["messages"]) if isinstance(msg, HumanMessage)),
        None,
    )
    if not last_user_message:
        raise ValueError("No user message found in the conversation")

    response = await model.ainvoke(state["messages"])
    tool_calls = response.tool_calls
    if not isinstance(response, AIMessage):
        raise ValueError("Agent response is not an AIMessage")
    if not tool_calls:
        raise ValueError("No tool calls found in agent response.")

    tool_names = {tool.name for tool in tools}
    if not all(tool_call["name"] in tool_names for tool_call in tool_calls):
        invalid_tool = next(
            tool_call["name"]
            for tool_call in response.tool_calls
            if tool_call["name"] not in tool_names
        )
        raise ValueError(
            f"Chosen tool '{invalid_tool}' is not in the list of available tools"
        )

    return {"messages": state["messages"] + [response]}


async def action(
    executor: ToolExecutor,
    stream_handler: AsyncStreamingCallbackHandler,
    state: AgentState,
) -> AgentState:
    """
    Executes the tool calls from the agent and streams the results back to the client
    through the tool executor.
    """
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        raise ValueError("Last message does not contain tool calls")

    tool_call = last_message.tool_calls[0]
    await stream_handler.on_tool_start(
        serialized=tool_call, input_str=tool_call["args"]
    )
    try:
        tool_result = await executor.ainvoke(
            ToolInvocation(tool=tool_call["name"], tool_input=tool_call["args"])
        )
    except Exception:
        user_friendly_message = (
            "I'm sorry, but there was an issue while invoking the tool."
        )
        await stream_handler.on_tool_error(
            error=UserFriendlyException(user_friendly_message),
            name=tool_call["name"],
        )
        logger.exception("Tool execution error")
        tool_result = user_friendly_message
    finally:
        await stream_handler.on_tool_end(name=tool_call["name"])
    return {
        "messages": [
            ToolMessage(
                tool_call_id=tool_call["id"],
                name=tool_call["name"],
                content=str(tool_result),
            )
        ]
    }


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
        should_continue_fn = partial(
            should_continue, get_llm_from_config(config, config.tool_call_llm)
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
            partial(
                agent,
                get_llm_from_config(config, config.tool_call_llm).bind_tools(tools),
                stream_handler,
                tools,
            ),
        )
        graph.add_node("action", partial(action, ToolExecutor(tools), stream_handler))

        graph.add_edge(START, "agent")
        graph.add_edge("agent", "action")
        graph.add_conditional_edges(
            "action", should_continue_fn, path_map={"continue": "agent", "end": END}
        )

        return cls(
            graph=graph.compile(),
            queue=queue,
            stop_event=stop_event,
            stream_handler=stream_handler,
        )

    async def process_queue(self) -> AsyncGenerator[str, None]:
        while not self.stop_event.is_set():
            try:
                item = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                yield item
                self.queue.task_done()
            except asyncio.TimeoutError:
                continue

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
            await self.stream_handler.on_llm_error(
                error=UserFriendlyException(error_message), **kwargs
            )
            logger.exception("There was an exception in the agent graph")
        finally:
            await self.stream_handler.on_llm_end()
            self.stop_event.set()  # TODO: Is this the best way to stop the graph?

        return result

    @staticmethod
    async def _streaming_function(queue: asyncio.Queue, data: StreamingData):
        await queue.put(data)
