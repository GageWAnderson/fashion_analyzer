from typing import Annotated, Sequence, Literal, Optional, TypedDict
import operator
from pydantic import BaseModel

from langchain.schema import BaseMessage
from langchain_core.documents import Document


def user_question_reducer(x: str, y: str) -> str:
    return y if y is not None else x


class RagState(TypedDict):
    user_question: Annotated[str, user_question_reducer]
    messages: Annotated[Sequence[BaseMessage], operator.add]
    docs: Annotated[list[Document], operator.add]
    output: Annotated[str, operator.add]


class DocumentGrade(BaseModel):
    grade: Literal["yes", "no"]
    reason: Optional[str]
