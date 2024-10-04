import json
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from typing import Optional


SourceType = Literal["web_page"]


class VectorMetadata(BaseModel):
    query: str = Field(..., description="The search query associated with this vector")
    url: str = Field(..., description="The URL of the source content")
    image_urls: Optional[str] = Field(
        default=None,
        description="JSON-formatted string containing a list of URLs for images extracted from the content",
    )
    chunk_id: str = Field(..., description="Unique identifier for this vector chunk")
    timestamp: str = Field(..., description="Timestamp of when this vector was created")
    source_type: str = Field(
        ..., description="Type of source (e.g., 'web_page', 'pdf', 'image')"
    )
    content_summary: Optional[str] = Field(
        default=None, description="A brief summary of the content"
    )
    relevance_score: Optional[float] = Field(
        default=None, description="Relevance score of this vector to the original query"
    )

    @field_validator("image_urls")
    def validate_image_urls(cls, v):
        if v is not None:
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("image_urls must be a valid JSON string")
        return v

    class Config:
        allow_population_by_field_name = True
