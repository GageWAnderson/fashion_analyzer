
from common.config.base_config import BaseConfig


class BackendConfig(BaseConfig):
    should_continue_prompt: str
    tool_call_llm: str
    tool_call_prompt: str
    max_tool_call_retries: int


backend_config = BackendConfig.from_yaml("app/config/config.yml")
