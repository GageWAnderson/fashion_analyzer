from typing import List
from common.config.base_config import BaseConfig


class CrawlerConfig(BaseConfig):
    init_message: str
    men_fashion_categories: List[str]
    women_fashion_categories: List[str]
    search_rephraser_prompt: str
    search_planner_prompt: str
    search_gender: str
    is_done_prompt: str
    fashion_summarizer_prompt: str
    chunk_format: str
    minio_presigned_url_expiry_days: int
    summarize_image_prompt: str
    summarize_content_prompt: str
    vision_llm: str

# TODO: Update the path if necessary
config = CrawlerConfig.from_yaml("crawler/config/config.yml")
