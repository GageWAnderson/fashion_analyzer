import asyncio

from typing import AsyncGenerator
from app.schemas.chat import Conversation
from app.utils.streaming import AsyncStreamingCallbackHandler, StreamingData
from app.utils.functional import compose
from app.graphs.chat import ChatGraph


def agent_chat(
    agent: ChatGraph, conversation: Conversation
) -> AsyncGenerator[str, None]:
    stop_event = asyncio.Event()
    queue = asyncio.Queue()

    async def process_queue() -> AsyncGenerator[str, None]:
        while not stop_event.is_set():
            try:
                item = await asyncio.wait_for(queue.get(), timeout=0.1)
                yield item
                queue.task_done()
            except asyncio.TimeoutError:
                continue

    async def streaming_function(data: StreamingData):
        await queue.put(data)

    asyncio.create_task(
        agent.ainvoke( # TODO: Enable LangGraph streaming with graph.stream()
            {"messages": conversation.load_messages()},
            config={
                "callbacks": [
                    AsyncStreamingCallbackHandler(streaming_function=streaming_function)
                ]
            },
        )
    )

    return process_queue()
