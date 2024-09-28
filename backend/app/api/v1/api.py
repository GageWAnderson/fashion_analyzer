__all__ = ["router"]

from fastapi import APIRouter
from api.v1.endpoints.agent import router

router = APIRouter()

router.include_router(router, prefix="/chat", tags=["chat"])
