# -*- coding: utf-8 -*-
from typing import Optional

from backend.app.api.dependencies import get_redis_client


async def is_running(run_id: Optional[str] = None) -> bool:
    redis_client = await get_redis_client()
    is_running_bool = await redis_client.get(run_id)
    return is_running_bool is not None


async def stop_run(run_id: str) -> None:
    redis_client = await get_redis_client()
    await redis_client.delete(run_id)
