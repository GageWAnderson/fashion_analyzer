from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from backend.app.graphs.rag import RagGraph
from backend.app.config.config import backend_config
from common.db.vector_store import ChromaVectorStore
from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from backend.app.schemas.rag import RagToolInput


class RagTool(BaseTool):
    name: str = "rag_tool"
    description: str = (
        """Use this tool to search your database to answer the user's question."""
    )
    args_schema: Type[BaseModel] = RagToolInput
    stream_handler: AsyncStreamingCallbackHandler = Field(default=None, exclude=True)

    def _run(self, input: str) -> str:
        raise NotImplementedError("RAG tool does not support sync execution.")

    async def _arun(self, input: str) -> str:
        vector_store = ChromaVectorStore.from_config(backend_config)
        rag_graph = RagGraph.from_config(
            backend_config, vector_store, self.stream_handler
        )
        return await rag_graph.ainvoke({"question": input})
