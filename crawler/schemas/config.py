import yaml
import os
from pydantic import BaseModel
from dotenv import load_dotenv


class CrawlerConfig(BaseModel):
    llm: str
    embedding_model: str
    vector_store_collection_name: str
    vector_search_type: str
    vector_search_k: int
    vector_search_fetch_k: int
    search_plan_retry_limit: int
    num_search_iterations: int
    init_message: str
    men_fashion_categories: list[str]
    women_fashion_categories: list[str]
    search_rephraser_prompt: str
    search_planner_prompt: str
    is_done_prompt: str
    fashion_summarizer_prompt: str
    chunk_format: str

    openai_api_key: str
    openai_model: str
    tavily_api_key: str
    user_agent: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    minio_root_user: str
    minio_root_password: str
    ollama_url: str
    chroma_host: str
    chroma_port: int

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "CrawlerConfig":
        load_dotenv()
        with open(yaml_path, "r") as file:
            yaml_data = yaml.safe_load(file)

        # Add environment variables to yaml_data
        yaml_data.update(
            {
                "openai_api_key": os.getenv("OPENAI_API_KEY"),
                "openai_model": os.getenv("OPENAI_MODEL"),
                "tavily_api_key": os.getenv("TAVILY_API_KEY"),
                "user_agent": os.getenv("USER_AGENT"),
                "postgres_user": os.getenv("POSTGRES_USER"),
                "postgres_password": os.getenv("POSTGRES_PASSWORD"),
                "postgres_db": os.getenv("POSTGRES_DB"),
                "minio_root_user": os.getenv("MINIO_ROOT_USER"),
                "minio_root_password": os.getenv("MINIO_ROOT_PASSWORD"),
                "ollama_url": os.getenv("OLLAMA_URL"),
                "chroma_host": os.getenv("CHROMA_HOST"),
                "chroma_port": int(os.getenv("CHROMA_PORT", 0)),
            }
        )

        return cls.model_validate(yaml_data)

# TODO: Refactor into a more robust yaml retrieval path
config = CrawlerConfig.from_yaml("crawler/config/config.yml")
