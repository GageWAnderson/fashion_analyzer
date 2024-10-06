__all__ = ["agent_router"]
import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.app.schemas.chat import Conversation
from backend.app.utils.async_iteration import ajoin
from backend.app.graphs.chat import ChatGraph
from backend.app.utils.runs import stop_run
from backend.app.api.dependencies import get_chat_graph

agent_router = APIRouter()


@agent_router.post("/agent")
async def agent(
    conversation: Conversation, chat_graph: ChatGraph = Depends(get_chat_graph)
) -> StreamingResponse:

    asyncio.create_task(
        chat_graph.ainvoke(
            {"messages": conversation.load_messages()},
        )
    )

    return StreamingResponse(
        ajoin(
            by="\n",
            items=chat_graph.process_queue(),
        ),
        media_type="text/plain-text",
    )


@agent_router.get("/run/{run_id}/cancel", response_model=bool)
async def run_cancel(
    run_id: str,
) -> bool:
    await stop_run(run_id)
    return True
