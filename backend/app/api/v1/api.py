__all__ = ["agent_router"]

from fastapi import APIRouter
from backend.app.api.v1.endpoints.agent import agent_router
from backend.app.api.v1.endpoints.summary import summary_router

router = APIRouter()

router.include_router(agent_router, prefix="/chat", tags=["chat"])
router.include_router(summary_router, prefix="/summary", tags=["summary"])
