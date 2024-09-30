import yaml
from pydantic import BaseModel


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

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "CrawlerConfig":
        with open(yaml_path, "r") as file:
            yaml_data = yaml.safe_load(file)
            return cls.model_validate(yaml_data)
