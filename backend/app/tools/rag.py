from typing import Annotated

from langchain_core.tools import tool
from langchain_core.tools import StructuredTool

from app.graphs.rag import RagGraph
from app.services.llm import get_llm
from app.core.config import settings
from app.db.vector_store import ChromaVectorStore


@tool
async def rag_tool(
    input: Annotated[str, "A search query to search Tavily for."]
) -> StructuredTool:
    """This tool uses a RAG (Retrieval Augmented Generation) model to answer a user's question using data in a vector database."""
    llm = get_llm(settings.RAG_TOOL_LLM)
    vector_store = ChromaVectorStore.from_config()
    rag_graph = RagGraph.from_dependencies(llm, vector_store)
    return rag_graph.ainvoke({"question": input})
