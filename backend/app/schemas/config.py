import yaml
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv


class BackendConfig(BaseSettings):
    llm: str
    tool_call_llm: str
    embedding_model: str
    vector_store_collection_name: str
    vector_search_type: str
    vector_search_k: int
    vector_search_fetch_k: int
    search_plan_retry_limit: int
    num_search_iterations: int
    should_continue_prompt: str
    tool_call_prompt: str
    logging_dir: str

    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(..., env="OPENAI_MODEL")
    tavily_api_key: str = Field(..., env="TAVILY_API_KEY")
    secret_key: str = Field(..., env="SECRET_KEY")
    user_agent: str = Field(..., env="USER_AGENT")
    project_name: str = Field(..., env="PROJECT_NAME")
    api_version: str = Field(..., env="API_VERSION")
    api_v1_str: str = Field(..., env="API_V1_STR")
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
    def from_yaml(cls, yaml_path: str) -> "BackendConfig":
        load_dotenv()
        with open(yaml_path, "r") as file:
            yaml_data = yaml.safe_load(file)

        return cls(**yaml_data)
