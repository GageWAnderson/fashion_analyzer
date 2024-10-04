import yaml
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
from typing import List


class CrawlerConfig(BaseSettings):
    llm: str
    embedding_model: str
    vector_store_collection_name: str
    vector_search_type: str
    vector_search_k: int
    vector_search_fetch_k: int
    search_plan_retry_limit: int
    num_search_iterations: int
    init_message: str
    men_fashion_categories: List[str]
    women_fashion_categories: List[str]
    search_rephraser_prompt: str
    search_planner_prompt: str
    is_done_prompt: str
    fashion_summarizer_prompt: str
    chunk_format: str
    minio_presigned_url_expiry_days: int

    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(..., env="OPENAI_MODEL")
    tavily_api_key: str = Field(..., env="TAVILY_API_KEY")
    user_agent: str = Field(..., env="USER_AGENT")
    redis_host: str = Field(..., env="REDIS_HOST")
    redis_port: int = Field(..., env="REDIS_PORT")
    redis_db: int = Field(..., env="REDIS_DB")
    redis_password: str = Field(..., env="REDIS_PASSWORD")
    postgres_user: str = Field(..., env="POSTGRES_USER")
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")
    postgres_db: str = Field(..., env="POSTGRES_DB")
    minio_root_user: str = Field(..., env="MINIO_ROOT_USER")
    minio_root_password: str = Field(..., env="MINIO_ROOT_PASSWORD")
    minio_host: str = Field(..., env="MINIO_HOST")
    minio_port: int = Field(..., env="MINIO_PORT")
    minio_bucket: str = Field(..., env="MINIO_BUCKET")
    minio_backend_user: str = Field(..., env="MINIO_BACKEND_USER")
    minio_backend_password: str = Field(..., env="MINIO_BACKEND_PASSWORD")
    ollama_url: str = Field(..., env="OLLAMA_URL")
    chroma_host: str = Field(..., env="CHROMA_HOST")
    chroma_port: int = Field(..., env="CHROMA_PORT")
    unstructured_api_key: str = Field(..., env="UNSTRUCTURED_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "CrawlerConfig":
        load_dotenv()
        with open(yaml_path, "r") as file:
            yaml_data = yaml.safe_load(file)

        return cls(**yaml_data)


# TODO: Refactor into a more robust yaml retrieval path
config = CrawlerConfig.from_yaml("crawler/config/config.yml")
