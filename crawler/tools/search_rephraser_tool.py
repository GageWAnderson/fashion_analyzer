import logging

from langchain_core.prompts import PromptTemplate

from crawler.config.config import CrawlerConfig
from crawler.schemas.state import WebCrawlerState
from crawler.schemas.search import SearchCategories
from common.utils.json import extract_json_from_markdown
from common.utils.llm import get_llm_from_config
from crawler.schemas.search import update_search_categories

logger = logging.getLogger(__name__)


def search_rephraser_tool(config: CrawlerConfig, state: WebCrawlerState):
    retries = 0
    search_rephraser_prompt_template = PromptTemplate.from_template(
        config.search_rephraser_prompt
    )
    llm = get_llm_from_config(config, config.tool_call_llm)

    while retries < config.search_plan_retry_limit:
        try:
            new_search_categories = llm.invoke(
                input=search_rephraser_prompt_template.format()
            )
            logger.debug(f"New Search categories: {new_search_categories}")
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
            logger.exception(
                f"There was an exception making the new search categories: {e}"
            )

    raise ValueError(
        f"Search planner failed to return valid JSON after {config.search_plan_retry_limit} retries."
    )
