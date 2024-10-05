__all__ = ["agent_router"]

from fastapi import APIRouter
from backend.app.api.v1.endpoints.agent import agent_router

router = APIRouter()

router.include_router(agent_router, prefix="/chat", tags=["chat"])
