import logging
from typing import Any, Sequence

from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langchain_core.messages import ToolMessage
from langchain.schema.runnable import RunnableConfig
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from backend.app.schemas.agent_state import AgentState
from backend.app.schemas.exceptions import UserFriendlyException

logger = logging.getLogger(__name__)


class ActionNode(Runnable[AgentState, AgentState]):
    def __init__(
        self,
        tools: Sequence[BaseTool],
        stream_handler: AsyncStreamingCallbackHandler,
    ):
        self.executor = ToolExecutor(tools)
        self.stream_handler = stream_handler

    def invoke(self, state: AgentState) -> AgentState:
        raise NotImplementedError("ActionNode does not support sync invoke")

    async def ainvoke(
        self,
        state: AgentState,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> AgentState:
        """
        Executes the tool calls from the agent and streams the results back to the client
        through the tool executor.
        """
        last_message = state["messages"][-1]
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            raise ValueError("Last message does not contain tool calls")

        tool_call = last_message.tool_calls[0]
        await self.stream_handler.on_tool_start(
            serialized=tool_call, input_str=tool_call["args"]
        )
        try:
            tool_result = await self.executor.ainvoke(
                ToolInvocation(tool=tool_call["name"], tool_input=tool_call["args"])
            )
        except Exception:
            user_friendly_message = (
                "I'm sorry, but there was an issue while invoking the tool."
            )
            await self.stream_handler.on_tool_error(
                error=UserFriendlyException(user_friendly_message),
                name=tool_call["name"],
            )
            logger.exception("Tool execution error")
            tool_result = user_friendly_message
        finally:
            await self.stream_handler.on_tool_end(name=tool_call["name"])
        return {
            "messages": [
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    name=tool_call["name"],
                    content=str(tool_result),
                )
            ]
        }
