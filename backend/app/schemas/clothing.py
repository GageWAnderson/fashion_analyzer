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
    Includes a variety of possible metadata fields.
    """

    id: Optional[str] = Field(
        None, description="Unique identifier for the clothing item"
    )
    name: Optional[str] = Field(
        None, description="Descriptive name of the clothing item"
    )
    brand: Optional[str] = Field(
        None, description="Manufacturer or designer of the clothing item"
    )
    category: Optional[str] = Field(
        None, description="General category of the item, e.g., shirts, pants, dresses"
    )
    subcategory: Optional[str] = Field(
        None,
        description="More specific classification, e.g., t-shirt, jeans, cocktail dress",
    )
    price: Optional[float] = Field(None, description="Current price of the item")
    original_price: Optional[float] = Field(
        None, description="Original price if the item is on sale"
    )
    image_url: Optional[str] = Field(None, description="URL of the item's image")
    color: Optional[str] = Field(None, description="Primary color of the item")
    sizes: Optional[list[str]] = Field(
        None, description="Available sizes or size range"
    )
    material: Optional[str] = Field(
        None, description="Main fabric or material composition"
    )
    gender: Optional[str] = Field(
        None, description="Target gender if applicable (men's, women's, unisex)"
    )
    season: Optional[str] = Field(
        None,
        description="Appropriate season for the item, e.g., summer, winter, all-season",
    )
    style: Optional[str] = Field(
        None, description="Style of the item, e.g., casual, formal, sporty"
    )
    description: Optional[str] = Field(
        None, description="Detailed text description of the item"
    )
    care_instructions: Optional[str] = Field(
        None, description="Instructions for washing and maintaining the item"
    )
    availability: Optional[str] = Field(
        None, description="Availability status, e.g., in stock, out of stock, pre-order"
    )
    average_rating: Optional[float] = Field(
        None, description="Average customer rating of the item"
    )
    num_reviews: Optional[int] = Field(None, description="Number of customer reviews")
    tags: Optional[list[str]] = Field(
        None,
        description="Keywords associated with the item for searching and categorization",
    )
    dimensions: Optional[dict] = Field(
        None, description="Measurements of the item, e.g., length, width, sleeve length"
    )
    weight: Optional[float] = Field(
        None, description="Weight of the item, useful for shipping calculations"
    )
    release_date: Optional[date] = Field(
        None, description="Date when the item was first available or added to inventory"
    )
    sustainability_info: Optional[str] = Field(
        None, description="Information about eco-friendly or ethical production"
    )


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
