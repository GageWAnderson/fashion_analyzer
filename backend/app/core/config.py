from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Settings for the application from the .env file.
    """

    PROJECT_NAME: str = "Fashion Analyzer"
    API_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_ORGANIZATION: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_API_BASE: Optional[str] = None

    OLLAMA_BASE_MODEL: str = "llama3.1"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text:latest"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    QA_TOOL_LLM: str = "llama3.1"

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
