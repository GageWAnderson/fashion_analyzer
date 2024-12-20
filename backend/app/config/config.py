from common.config.base_config import BaseConfig


class BackendConfig(BaseConfig):
    should_continue_prompt: str
    tool_call_llm: str
    summarize_llm: str
    summarize_docs_prompt: str
    max_tool_call_retries: int
    max_search_results: int
    max_retries: int
    max_clothing_items_to_stream: int
    max_images_to_display: int
    summarize_weekly_prompt: str
    summarize_docs_prompt_no_images: str
    min_sources_for_summary: int
    select_action_plan_prompt: str
    question_filter_prompt: str
    clothing_extractor_prompt: str
    max_clothing_search_retries: int
    clothing_search_result_parser_prompt: str
    html_contains_clothing_info_prompt: str
    is_clothing_product_link_prompt: str
    chunk_size: int
    chunk_overlap: int
    chunk_batch_size: int
    max_queue_size: int
    clothing_parser_timeout: float
    link_click_timeout: float


backend_config = BackendConfig.from_yaml("backend/app/config/config.yml")
