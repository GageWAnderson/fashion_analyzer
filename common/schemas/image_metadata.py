

from pydantic import BaseModel


class ImageMetadata(BaseModel):
    url: str
    summary: str
