import redis
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import image_analysis, other_routes
from app.core import config

app = FastAPI()

# Initialize Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.Redis.from_url(redis_url)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(image_analysis.router)
app.include_router(other_routes.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Fashion Analyzer API"}
