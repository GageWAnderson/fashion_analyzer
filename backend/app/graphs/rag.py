from typing import Union, Any

from langgraph.graph import StateGraph, START, END

from backend.app.config.config import BackendConfig
from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from common.db.vector_store import PgVectorStore
from backend.app.schemas.agent_state import AgentState
from backend.app.nodes.retrieve import RetrieveNode
from backend.app.nodes.summarize_docs import SummarizeDocsNode
from backend.app.schemas.subgraph import Subgraph


class RagGraph(Subgraph):
    """
    This graph answers questions about the most current fashion trends you have gathered from the internet
    in the past year. Use this tool when your user wants the most up-to-date advice and trends.
    """

    name: str = "rag_graph"
    description: str = (
        """Answers questions about the most current fashion trends 
        you have gathered from the internet in the past year. 
        Use this tool when your user wants the most up-to-date advice and trends.
        """
    )
    stream_handler: AsyncStreamingCallbackHandler

    @classmethod
    def from_config(
        cls,
        config: BackendConfig,
        vector_store: PgVectorStore,
        stream_handler: AsyncStreamingCallbackHandler,
    ) -> "RagGraph":
        graph = StateGraph(AgentState)

        graph.add_node("retrieve", RetrieveNode(vector_store))
        # graph.add_node("grade_docs", GradeDocsNode(stream_handler))
        graph.add_node("summarize", SummarizeDocsNode(stream_handler))

        graph.add_edge(START, "retrieve")
        graph.add_edge("retrieve", "summarize")
        # TODO: Re-enable doc grading once RAG performance is improved
        # graph.add_edge("retrieve", "grade_docs")
        # graph.add_edge("grade_docs", "summarize")
        graph.add_edge("summarize", END)

        return cls(
            name=cls.get_name(),
            description=cls.get_description(),
            graph=graph.compile(),
            stream_handler=stream_handler,
        )

    async def ainvoke(self, *args, **kwargs) -> Union[dict[str, Any], Any]:
        """
        Answers questions about the most current fashion trends you have gathered from the internet
        in the past year. Use this tool when your user wants the most up-to-date advice and trends.
        """
        return self.graph.ainvoke(
            {"question": input}, config={"callbacks": [self.stream_handler]}
        )
