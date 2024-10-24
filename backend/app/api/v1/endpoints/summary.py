__all__ = ["summary_router"]

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.summary import WeeklySummaryResponse
from backend.app.services.summary import SummaryService
from backend.app.config.config import backend_config
from backend.app.exceptions.sources import NotEnoughSourcesException

logger = logging.getLogger(__name__)
summary_router = APIRouter()


async def get_summary_service() -> SummaryService:
    return await SummaryService.from_config(backend_config)


@summary_router.get("/weekly/text")
async def get_weekly_summary_text(
    # summary_service: SummaryService = Depends(get_summary_service),
) -> WeeklySummaryResponse:  # TODO: Add user settings to the summary
    summary_service = await get_summary_service()
    try:
        return await summary_service.generate_summary(weeks=1, days=0)
    except NotEnoughSourcesException as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error generating the summary",
        )
