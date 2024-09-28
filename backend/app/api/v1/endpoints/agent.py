__all__ = ["router"]
from functools import partial

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import Conversation
from utils.functional import ajoin
from app.graphs.chat import ChatGraph
from app.services.agent import agent_chat
from app.core.config import settings
from app.services.llm import get_llm, get_tools

router = APIRouter()

agent_chat = partial(
    agent_chat,
    ChatGraph.from_dependencies(
        get_llm(settings.OPENAI_MODEL, settings.OPENAI_API_KEY), get_tools()
    ),
)


@router.post("/agent")
async def agent(conversation: Conversation) -> StreamingResponse:
    return StreamingResponse(
        ajoin(
            by="\n",
            items=agent_chat(conversation),
            media_type="text/plain-text",
        )
    )
