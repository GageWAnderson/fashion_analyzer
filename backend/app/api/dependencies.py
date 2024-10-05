from redis import Redis as RedisSync
from redis import Redis
from redis import asyncio as aioredis

from app.config.config import config


def get_redis_client_sync() -> RedisSync:
    """Returns a synchronous Redis client."""
    return RedisSync(
        host=config.redis_host,
        port=config.redis_port,
        db=0,
        decode_responses=True,
    )


async def get_redis_client() -> Redis:
    """Returns an asynchronous Redis client as a coroutine function which should be
    awaited."""
    return await aioredis.from_url(
        f"redis://{config.redis_host}:{config.redis_port}",
        max_connections=10,
        encoding="utf8",
        decode_responses=True,
    )
