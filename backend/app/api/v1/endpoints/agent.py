__all__ = ["agent_router"]
from functools import partial

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import Conversation
from app.utils.async_iteration import ajoin
from app.graphs.chat import ChatGraph
from app.services.agent import agent_chat
from app.core.config import settings
from app.services.llm import get_llm
from app.tools.qa import qa_tool
from app.tools.search import search_tool
from app.utils.runs import stop_run

agent_router = APIRouter()

agent_chat = partial(
    agent_chat,
    ChatGraph.from_dependencies(
        get_llm(settings.OLLAMA_BASE_MODEL),
        [qa_tool, search_tool, rag_tool],
    ),
)


@agent_router.post("/agent")
async def agent(conversation: Conversation) -> StreamingResponse:
    return StreamingResponse(
        ajoin(
            by="\n",
            items=agent_chat(conversation),
        ),
        media_type="text/plain-text",
    )


@agent_router.get("/run/{run_id}/cancel", response_model=bool)
async def run_cancel(
    run_id: str,
) -> bool:
    await stop_run(run_id)
    return True
