from typing import Annotated, Sequence, TypedDict
import operator
from langchain.schema import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
