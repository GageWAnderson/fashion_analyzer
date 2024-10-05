from typing import Annotated

from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import StructuredTool


@tool
async def search_tool(
    input: Annotated[str, "A search query to search Tavily for."]
) -> StructuredTool:
    """This tool searches Tavily for information relevant to the user's query."""
    tavily_search = TavilySearchResults()
    return tavily_search.invoke({"query": input})
