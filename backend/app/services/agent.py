import asyncio

from typing import AsyncGenerator
from app.schemas.chat import Conversation
from app.utils.streaming import AsyncStreamingCallbackHandler, StreamingData
from app.utils.functional import compose
from app.graphs.chat import ChatGraph


def agent_chat(
    agent: ChatGraph, conversation: Conversation
) -> AsyncGenerator[str, None]:
    stop = asyncio.Event()
    queue = asyncio.Queue(stop=stop)

    asyncio.create_task(
        agent.invoke(
            {"messages": conversation.load_messages()},
            config={
                "callbacks": [
                    AsyncStreamingCallbackHandler(
                        streaming_function=compose(queue.put, StreamingData)
                    )
                ]
            },
        )
    )

    return queue
