from typing import Optional

from pydantic import BaseModel, ConfigDict

from langchain_core.runnables import Runnable, RunnableConfig

from backend.app.schemas.agent_state import AgentState
from backend.app.utils.streaming import AsyncStreamingCallbackHandler


class SubgraphStartNode(BaseModel, Runnable):
    """
    Runnable that initializes the subgraph tool.
    """

    name: str
    stream_handler: AsyncStreamingCallbackHandler
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_handler(
        cls, name: str, stream_handler: AsyncStreamingCallbackHandler
    ) -> "SubgraphStartNode":
        return cls(name=name, stream_handler=stream_handler)

    @classmethod
    def get_name(cls) -> str:
        return cls.name

    def invoke(self, *args, **kwargs) -> None:
        raise NotImplementedError("SubgraphStartNode does not support sync invoke")

    async def ainvoke(
        self, state: AgentState, config: Optional[RunnableConfig], **kwargs
    ) -> AgentState:
        await self.stream_handler.on_tool_start(self.name)
        return {"selected_tool": self.name}
