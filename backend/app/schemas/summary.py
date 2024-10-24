from pydantic import BaseModel


class WeeklySummaryResponse(BaseModel):
    text: str
    sources: list[str]
    images: list[str]
