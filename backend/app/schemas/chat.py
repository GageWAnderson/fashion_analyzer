# -*- coding: utf-8 -*-
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union
from uuid import UUID

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field, StrictBool, StrictFloat, StrictInt

from backend.app.schemas.common import CamelCaseModel

LangchainMessage = Union[
    AIMessage,
    HumanMessage,
    SystemMessage,
]


class MessageRole(
    str,
    Enum,
):
    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"


class UserSettings(BaseModel):
    data: dict[
        str,
        Any,
    ]
    version: Optional[int] = None


class ChatMessage(CamelCaseModel):
    role: MessageRole
    content: str

    def to_langchain(
        self,
    ) -> LangchainMessage | None:
        match self.role:
            case MessageRole.SYSTEM:
                return SystemMessage(content=self.content)
            case MessageRole.USER:
                return HumanMessage(content=self.content)
            case MessageRole.AGENT:
                return AIMessage(content=self.content)
            case _:
                return None


class Conversation(CamelCaseModel):
    messages: list[ChatMessage]
    conversation_id: UUID
    new_message_id: UUID
    user_email: str
    settings: Optional[UserSettings]

    def load_messages(self) -> list[LangchainMessage]:
        return [message.to_langchain() for message in self.messages]
