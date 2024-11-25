from typing import Optional

from pydantic import BaseModel, ConfigDict

from langchain_core.runnables import Runnable, RunnableConfig

from backend.app.schemas.agent_state import AgentState
from backend.app.utils.streaming import AsyncStreamingCallbackHandler


class EndNode(BaseModel, Runnable):
    """
    Runnable that send the graph finish signal to the frontend
    before terminating the graph.
    """

    name: str = "end_node"
    stream_handler: Optional[AsyncStreamingCallbackHandler] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_handler(
        cls, stream_handler: Optional[AsyncStreamingCallbackHandler] = None
    ) -> "EndNode":
        return cls(stream_handler=stream_handler)

    @classmethod
    def get_name(cls) -> str:
        return cls.name

    def invoke(self, *args, **kwargs) -> None:
        raise NotImplementedError("EndNode does not support sync invoke")

    async def ainvoke(
        self, state: AgentState, config: Optional[RunnableConfig], **kwargs
    ) -> AgentState:
        # TODO: Currently the agent can only call one subgraph tool per user question
        # TODO: Will need to move on_tool_end to another node to call multiple subgraph tools per user question
        if self.stream_handler:
            await self.stream_handler.on_tool_end(state["selected_tool"])
            await self.stream_handler.on_graph_end()
        return state
