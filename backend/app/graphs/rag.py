from typing import Union, Any

from pydantic import BaseModel

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from backend.app.config.config import BackendConfig
from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from common.db.vector_store import ChromaVectorStore
from backend.app.schemas.rag import RagGraphState
from backend.app.nodes.retrieve import RetrieveNode
from backend.app.nodes.grade_docs import GradeDocsNode
from backend.app.nodes.summarize_docs import SummarizeDocsNode
from common.utils.llm import get_llm_from_config


class RagGraph(BaseModel):
    graph: CompiledStateGraph

    @classmethod
    def from_config(
        cls,
        config: BackendConfig,
        vector_store: ChromaVectorStore,
        stream_handler: AsyncStreamingCallbackHandler,
    ) -> "RagGraph":
        graph = StateGraph(RagGraphState)
        llm = get_llm_from_config(config)

        graph.add_node("retrieve", RetrieveNode(vector_store))
        graph.add_node("grade_docs", GradeDocsNode(llm, stream_handler))
        graph.add_node("summarize", SummarizeDocsNode(llm, stream_handler))

        graph.add_edge(START, "retrieve")
        graph.add_edge("retrieve", "grade_docs")
        graph.add_edge("grade_docs", "summarize")
        graph.add_edge("summarize", END)

        return graph.compile()

    async def ainvoke(self, *args, **kwargs) -> Union[dict[str, Any], Any]:
        """
        Answers questions about the most current fashion trends you have gathered from the internet
        in the past year. Use this tool when your user wants the most up-to-date advice and trends.
        """
        return self.graph.ainvoke({"question": input})
