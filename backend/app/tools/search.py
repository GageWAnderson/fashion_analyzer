from typing import Annotated, Type

from langchain_core.tools import BaseTool
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults

from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from backend.app.config.config import backend_config
from common.utils.llm import get_llm_from_config


class SearchToolInput(BaseModel):
    input: Annotated[str, "A search query to search Tavily for."]


class SearchTool(BaseTool):
    name: str = "search_tool"
    description: str = (
        "This tool searches Tavily for information relevant to the user's query."
    )
    args_schema: Type[BaseModel] = SearchToolInput
    stream_handler: AsyncStreamingCallbackHandler = Field(default=None, exclude=True)

    def _run(self, input: str) -> str:
        raise NotImplementedError("Search tool does not support sync.")

    async def _arun(self, input: str) -> str:
        tavily_search = TavilySearchResults()
        search_results = tavily_search.invoke({"query": input})
        llm = get_llm_from_config(backend_config)
        return await llm.ainvoke(search_results)
