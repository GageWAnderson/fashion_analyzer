from typing import TypedDict, Annotated, Literal, Optional
import operator

from langchain_core.documents import Document
from pydantic import BaseModel


class RagToolInput(BaseModel):
    input: Annotated[str, "A search query to search the vector database for."]


class DocumentGrade(BaseModel):
    grade: Literal["yes", "no"]
    reason: Optional[str]


class RagGraphState(TypedDict):
    question: Annotated[str, operator.add]
    docs: Annotated[list[Document], operator.add]
    answer: Annotated[str, operator.add]
    search: Annotated[str, operator.add]
