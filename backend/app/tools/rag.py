from typing import Annotated

from langchain_core.tools import tool
from langchain_core.tools import StructuredTool

from backend.app.graphs.rag import RagGraph
from backend.app.config.config import backend_config
from common.db.vector_store import ChromaVectorStore
from backend.app.utils.streaming import AsyncStreamingCallbackHandler


@tool # TODO: Change this to a class rather than a function
async def rag_tool(
    stream_handler: AsyncStreamingCallbackHandler,
    input: Annotated[str, "A search query to search Tavily for."],
) -> StructuredTool:
    """
    This tool uses a RAG (Retrieval Augmented Generation) model to answer
    user's questions with stored information from the vector database."""
    vector_store = ChromaVectorStore.from_config(backend_config)
    rag_graph = RagGraph.from_config(backend_config, vector_store, stream_handler)
    return rag_graph.ainvoke({"question": input})
