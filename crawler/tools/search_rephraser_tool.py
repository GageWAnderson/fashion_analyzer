from langchain_core.prompts import PromptTemplate

from crawler.config.config import CrawlerConfig
from crawler.schemas.state import WebCrawlerState
from crawler.schemas.search import SearchCategories
from crawler.utils.json import extract_json_from_markdown
from crawler.utils.llm import get_llm
from crawler.schemas.search import update_search_categories


def search_rephraser_tool(config: CrawlerConfig, state: WebCrawlerState):
    retries = 0
    search_rephraser_prompt_template = PromptTemplate.from_template(
        config.search_rephraser_prompt
    )
    llm = get_llm(config.llm)
    while retries < config.search_plan_retry_limit:
        try:
            new_search_categories = llm.invoke(
                input=search_rephraser_prompt_template.format()
            )
            print(f"New Search categories: {new_search_categories}")
            new_categories = SearchCategories.model_validate_json(
                extract_json_from_markdown(new_search_categories.content)
            )
            return {
                "messages": state["messages"],
                "search_categories": update_search_categories(
                    state["search_categories"], new_categories.categories
                ),
            }
        except Exception as e:
            retries += 1
            print(f"There was an exception making the new search categories: {e}")

    raise ValueError(
        f"Search planner failed to return valid JSON after {config.search_plan_retry_limit} retries."
    )
