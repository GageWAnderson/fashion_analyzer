import logging

from langchain_core.prompts import PromptTemplate

from crawler.config.config import CrawlerConfig
from crawler.schemas.state import WebCrawlerState
from crawler.schemas.search import SearchCategories
from common.utils.llm import get_llm_from_config
from crawler.schemas.search import update_search_categories

logger = logging.getLogger(__name__)


async def search_rephraser_tool(config: CrawlerConfig, state: WebCrawlerState):
    retries = 0
    search_rephraser_prompt_template = PromptTemplate.from_template(
        config.search_rephraser_prompt
    )
    # llm = get_llm_from_config(config, config.tool_call_llm).with_structured_output(
    #     SearchCategories
    # )
    structured_llm = get_llm_from_config(config, config.tool_call_llm)

    while retries < config.search_plan_retry_limit:
        try:
            new_search_categories = await structured_llm.ainvoke_with_tools(
                search_rephraser_prompt_template.format(),
                tools=[get_search_categories_oai_function()],
            )
            logger.debug(f"New Search categories: {new_search_categories}")
            valid_search_categories = extract_valid_search_categories(
                new_search_categories
            )
            return {
                "messages": state["messages"],
                "search_categories": update_search_categories(
                    state["search_categories"], valid_search_categories
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


def extract_valid_search_categories(raw_categories: dict) -> list[str]:
    return raw_categories["categories"]


def get_search_categories_oai_function() -> dict:
    description = """
Given the state, return a JSON-formatted list of search categories.
The new search categories should be a list of strings.
"""
    return {
        "type": "function",
        "function": {
            "name": "get_search_categories",
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
    }
