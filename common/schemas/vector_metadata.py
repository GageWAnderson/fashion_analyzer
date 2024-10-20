from typing import Literal

from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationError
from typing import Optional

from common.schemas.image_metadata import ImageMetadata

SourceType = Literal["web_page"]


class VectorMetadata(BaseModel):
    query: str = Field(..., description="The search query associated with this vector")
    url: str = Field(..., description="The URL of the source content")
    image_metadata: Optional[list[dict]] = Field(
        default=None, description="Metadata for images extracted from the content"
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
    model_config: ConfigDict = ConfigDict(populate_by_name=True)

    @field_validator("source_type")
    def validate_source_type(cls, v):
        if v not in SourceType.__args__:
            raise ValueError(
                f"Invalid source_type. Must be one of: {', '.join(SourceType.__args__)}"
            )
        return v

    # TODO: Expand this to support other media types
    @field_validator("image_metadata")
    def validate_image_metadata(cls, v):
        # Validate that each element in v is a valid ImageMetadata object
        for image_metadata in v:
            try:
                ImageMetadata(**image_metadata)
            except ValidationError as e:
                raise ValueError(f"Invalid image_metadata: {e}")
        return v
