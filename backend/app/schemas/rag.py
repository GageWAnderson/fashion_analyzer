from typing import Literal, Optional

from pydantic import BaseModel


class DocumentGrade(BaseModel):
    grade: Literal["yes", "no"]
    reason: Optional[str]
