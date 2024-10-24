__all__ = ["summary_router"]

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.summary import WeeklySummaryResponse
from backend.app.services.summary import SummaryService
from backend.app.config.config import backend_config
from backend.app.exceptions.sources import NotEnoughSourcesException

summary_router = APIRouter()


def get_summary_service() -> SummaryService:
    return SummaryService.from_config(backend_config)


@summary_router.get("/weekly/text")
async def get_weekly_summary_text(
    summary_service: SummaryService = Depends(get_summary_service),
) -> WeeklySummaryResponse:  # TODO: Add user settings to the summary
    try:
        return await summary_service.generate_summary(weeks=1, days=0)
    except NotEnoughSourcesException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message
        )
