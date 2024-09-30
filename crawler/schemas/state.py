from typing import Annotated
from typing_extensions import TypedDict

from pydantic import BaseModel

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from crawler.schemas.search import (
    SearchPlans,
    increment_search_iterations,
    update_search_categories,
    update_search_plans,
)


class WebCrawlerState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    search_plans: Annotated[SearchPlans, update_search_plans]
    num_search_iterations: Annotated[int, increment_search_iterations]
    search_categories: Annotated[list[str], update_search_categories]
