from typing import Annotated

from langchain_core.tools import tool
from langchain_core.tools import StructuredTool

from backend.app.graphs.rag import RagGraph
from backend.app.config.config import backend_config
from common.db.vector_store import ChromaVectorStore


@tool
async def rag_tool(
    input: Annotated[str, "A search query to search Tavily for."]
) -> StructuredTool:
    """This tool uses a RAG (Retrieval Augmented Generation) model to answer a user's question using data in a vector database."""
    vector_store = ChromaVectorStore.from_config(backend_config)
    rag_graph = RagGraph.from_config(backend_config, vector_store)
    return rag_graph.ainvoke({"question": input})
