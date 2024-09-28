__all__ = ["api_router"]

from fastapi import APIRouter
from api.v1.endpoints.agent import agent_router

api_router = APIRouter()

api_router.include_router(agent_router, prefix="/chat", tags=["chat"])
