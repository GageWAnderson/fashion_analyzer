import gc
import logging
import jwt
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from contextlib import asynccontextmanager
from langchain.globals import set_llm_cache
from langchain.cache import RedisCache
from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import api
from app.api.dependencies import get_redis_client, get_redis_client_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def user_id_identifier(request: Request) -> str:
    """Identify the user from the request."""
    if request.scope["type"] == "http":
        # Retrieve the Authorization header from the request
        auth_header = request.headers.get("Authorization")

        if auth_header is not None:
            # Check that the header is in the correct format
            header_parts = auth_header.split()
            if len(header_parts) == 2 and header_parts[0].lower() == "bearer":
                token = header_parts[1]
                try:
                    payload = jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=["HS256"],
                    )
                except (
                    jwt.JWTError,
                    ValidationError,
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Could not validate credentials",
                    )
                user_id = payload["sub"]
                print(
                    "here2",
                    user_id,
                )
                return user_id

    if request.scope["type"] == "websocket":
        return request.scope["path"]

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]

    ip = request.client.host if request.client else ""
    return ip + ":" + request.scope["path"]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Start up and shutdown tasks."""
    # TODO: Load yaml configs

    redis_client = await get_redis_client()
    set_llm_cache(RedisCache(redis_=get_redis_client_sync()))

    FastAPICache.init(
        RedisBackend(redis_client),
        prefix="fastapi-cache",
    )
    await FastAPILimiter.init(
        redis_client,
        identifier=user_id_identifier,
    )

    logger.info("Start up FastAPI [Full dev mode]")
    yield

    # shutdown
    await FastAPICache.clear()
    await FastAPILimiter.close()
    gc.collect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)

set_llm_cache(RedisCache(redis_=get_redis_client_sync()))


@app.get("/")
async def root():
    return {"message": "Welcome to the Fashion Analyzer API"}
