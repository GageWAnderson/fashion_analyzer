from common.config.base_config import BaseConfig


class BackendConfig(BaseConfig):
    should_continue_prompt: str
    tool_call_llm: str
    summarize_docs_prompt: str
    max_tool_call_retries: int
    summarize_weekly_prompt: str
    summarize_docs_prompt_no_images: str
    min_sources_for_summary: int
    select_action_plan_prompt: str


backend_config = BackendConfig.from_yaml("app/config/config.yml")
