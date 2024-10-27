# TODO: Implement a LangGraph sub-graph for clothing search
from typing import Any, Union

from langgraph.graph.state import StateGraph

from backend.app.config.config import BackendConfig
from backend.app.schemas.subgraph import Subgraph
from backend.app.schemas.agent_state import AgentState
from backend.app.utils.streaming import AsyncStreamingCallbackHandler


class ClothingSearchGraph(Subgraph):
    """
    This graph searches the web for clothing items similar to the one the user is asking about.
    """

    name: str = "clothing_search_graph"
    description: str = (
        "Searches the web for clothing items similar to the one the user is asking about."
    )
    stream_handler: AsyncStreamingCallbackHandler

    @classmethod
    def from_config(
        cls,
        config: BackendConfig,
        stream_handler: AsyncStreamingCallbackHandler,
    ) -> "ClothingSearchGraph":
        graph = StateGraph(AgentState)

        return cls(
            name=cls.get_name(),
            description=cls.get_description(),
            graph=graph.compile(),
            stream_handler=stream_handler,
        )

    async def ainvoke(self, *args, **kwargs) -> Union[dict[str, Any], Any]:
        """
        Searches the web for clothing items similar to the one the user is asking about.
        """
        return self.graph.ainvoke(
            {"question": input}, config={"callbacks": [self.stream_handler]}
        )
