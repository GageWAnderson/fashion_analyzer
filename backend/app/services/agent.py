import asyncio

from typing import AsyncGenerator
from backend.app.schemas.chat import Conversation
from backend.app.graphs.chat import ChatGraph


def agent_chat(
    agent: ChatGraph, conversation: Conversation
) -> AsyncGenerator[str, None]:

    asyncio.create_task(
        agent.ainvoke(
            {"messages": conversation.load_messages()},
        )
    )

    return agent.process_queue()
