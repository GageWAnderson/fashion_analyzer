import yaml
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

from common.config.base_config import BaseConfig


class BackendConfig(BaseConfig):
    should_continue_prompt: str
    tool_call_llm: str
    tool_call_prompt: str


backend_config = BackendConfig.from_yaml("app/config/config.yml")
