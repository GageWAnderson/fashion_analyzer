from redis import Redis as RedisSync
from redis import Redis
from redis import asyncio as aioredis

from backend.app.config.config import backend_config
from backend.app.graphs.chat import ChatGraph


def get_redis_client_sync() -> RedisSync:
    """Returns a synchronous Redis client."""
    return RedisSync(
        host=backend_config.redis_host,
        port=backend_config.redis_port,
        db=0,
        decode_responses=True,
    )


async def get_redis_client() -> Redis:
    """Returns an asynchronous Redis client as a coroutine function which should be
    awaited."""
    return await aioredis.from_url(
        f"redis://{backend_config.redis_host}:{backend_config.redis_port}",
        max_connections=10,
        encoding="utf8",
        decode_responses=True,
    )


def get_chat_graph():
    return ChatGraph.from_config(
        backend_config,
    )
