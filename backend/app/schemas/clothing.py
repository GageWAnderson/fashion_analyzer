from typing import Optional, TypedDict, Annotated, Sequence
import operator
from pydantic import BaseModel, Field
from datetime import date

from langchain.schema import BaseMessage

from common.utils.reducer import reduce_dict


class ClothingSearchQuery(BaseModel):
    """
    Key information for querying the web to search for clothing items.
    """

    query: str = Field(
        ..., description="The user's query rephrased for searching the web for clothes."
    )


# TODO: May need to have fewer fields to not confuse the LLM on extraction
class ClothingItem(BaseModel):
    """
    A clothing item extracted from the internet.
    """

    name: str = Field(..., description="Descriptive name of the clothing item")
    price: Optional[float] = Field(None, description="Current price of the item")
    image_url: Optional[str] = Field(None, description="URL of the item's image")
    link: Optional[str] = Field(None, description="URL of the item's page")


class ClothingItemList(BaseModel):
    """
    A wrapper class for a list of clothing items.
    Used to make sure LLMs called with .with_structured_output() return the correct type.
    """

    clothing_items: list[ClothingItem]


class ClothingGraphState(BaseModel):
    user_question: Annotated[str, operator.add]
    messages: Annotated[Sequence[BaseMessage], operator.add]
    selected_tool: Annotated[str, operator.add]
    search_item: Annotated[Optional[ClothingSearchQuery], reduce_dict] = Field(
        default=None, description="The search query for the web."
    )
    search_results: Annotated[list[dict], operator.add] = Field(
        default_factory=list, description="The raw results from Tavily search."
    )
    parsed_results: Annotated[list[ClothingItem], operator.add] = Field(
        default_factory=list, description="The parsed results from the search."
    )
    search_retries: Annotated[int, operator.add] = Field(
        -1, description="Number of times the search has been retried."
    )
