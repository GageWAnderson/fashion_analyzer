from typing import Annotated, Sequence, TypedDict
import operator
from langchain.schema import BaseMessage


class AgentState(TypedDict):
    user_question: Annotated[str, operator.add]
    messages: Annotated[Sequence[BaseMessage], operator.add]
