from typing import Annotated, Sequence, Literal, Optional, TypedDict
import operator
from pydantic import BaseModel

from langchain.schema import BaseMessage
from langchain_core.documents import Document


class RagState(TypedDict):
    user_question: Annotated[str, operator.add]
    messages: Annotated[Sequence[BaseMessage], operator.add]
    docs: Annotated[list[Document], operator.add]


class DocumentGrade(BaseModel):
    grade: Literal["yes", "no"]
    reason: Optional[str]
