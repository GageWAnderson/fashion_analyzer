from typing import Annotated

from langchain_core.tools import tool
from langchain_core.tools import StructuredTool

from app.graphs.rag import RagGraph
from app.services.llm import get_llm
from app.config.config import config
from app.db.vector_store import ChromaVectorStore


@tool
async def rag_tool(
    input: Annotated[str, "A search query to search Tavily for."]
) -> StructuredTool:
    """This tool uses a RAG (Retrieval Augmented Generation) model to answer a user's question using data in a vector database."""
    vector_store = ChromaVectorStore.from_config(config)
    rag_graph = RagGraph.from_config(config, vector_store)
    return rag_graph.ainvoke({"question": input})
