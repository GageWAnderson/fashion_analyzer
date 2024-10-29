from typing import Optional
import logging

from langchain_core.runnables import Runnable, RunnableConfig
from langchain_community.tools.tavily_search import TavilySearchResults

from backend.app.schemas.clothing import ClothingGraphState
from backend.app.config.config import backend_config

logger = logging.getLogger(__name__)


class ClothingSearchNode(Runnable[ClothingGraphState, ClothingGraphState]):

    def invoke(self, state: ClothingGraphState) -> ClothingGraphState:
        raise NotImplementedError("ClothingSearchNode does not support sync invoke")

    async def ainvoke(
        self, state: ClothingGraphState, config: Optional[RunnableConfig] = None
    ) -> ClothingGraphState:
        tavily_search = TavilySearchResults(
            max_results=backend_config.max_search_results
        )
        search_results = await tavily_search.ainvoke({"query": state.search_item.query})
        return {
            "search_results": search_results,
            "search_retries": state.search_retries + 1,
        }
