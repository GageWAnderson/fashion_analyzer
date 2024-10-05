import yaml
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

from common.config.base_config import BaseConfig


class BackendConfig(BaseConfig):
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


config = BackendConfig.from_yaml("app/config/config.yml")
