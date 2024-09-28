from redis import Redis as RedisSync
from redis import Redis
import aioredis

from app.core.config import settings


def get_redis_client_sync() -> RedisSync:
    """Returns a synchronous Redis client."""
    return RedisSync(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True,
    )


async def get_redis_client() -> Redis:
    """Returns an asynchronous Redis client as a coroutine function which should be
    awaited."""
    return await aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        max_connections=10,
        encoding="utf8",
        decode_responses=True,
    )
