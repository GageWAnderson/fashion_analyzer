from typing import Annotated

from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import StructuredTool

from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from backend.app.config.config import backend_config
from common.utils.llm import get_llm_from_config


@tool # TODO: Change this to a class rather than a function
async def search_tool(
    stream_handler: AsyncStreamingCallbackHandler,
    input: Annotated[str, "A search query to search Tavily for."],
) -> StructuredTool:
    """This tool searches Tavily for information relevant to the user's query."""
    tavily_search = TavilySearchResults()
    search_results = tavily_search.invoke({"query": input})
    llm = get_llm_from_config(backend_config)
    return llm.ainvoke(search_results, callbacks=[stream_handler])
