import logging
import json

from langchain_core.prompts import PromptTemplate

from crawler.config.config import CrawlerConfig
from crawler.schemas.state import WebCrawlerState
from crawler.schemas.search import SearchPlan, SearchPlans
from common.utils.time import get_current_year_and_month
from common.utils.llm import get_llm_from_config

logger = logging.getLogger(__name__)


# TODO Refactor into a LangChain tool with a from_config method
async def search_planner_tool(config: CrawlerConfig, state: WebCrawlerState):
    retries = 0
    search_planner_prompt_template = PromptTemplate.from_template(
        config.search_planner_prompt
    )
    structured_llm = get_llm_from_config(config, config.tool_call_llm)

    def search_planner_prompt(state: WebCrawlerState) -> PromptTemplate:
        current_year, current_month = get_current_year_and_month()
        return search_planner_prompt_template.format(
            state=state,
            current_year=current_year,
            current_month=current_month,
            search_gender=config.search_gender,
            categories=",\n".join(state["search_categories"]),
        )

    while retries < config.search_plan_retry_limit:
        try:
            raw_search_plan = await structured_llm.ainvoke_with_tools(
                search_planner_prompt(state),
                tools=[get_search_plan_oai_function()],
            )
            logger.info(f"Raw search plan: {raw_search_plan}")

            valid_search_plans = extract_valid_search_plans(raw_search_plan)
            return {
                "messages": state["messages"],
                "search_plans": SearchPlans(plans=valid_search_plans),
            }
        except Exception:
            logger.exception("Retrying search plan extraction")
            retries += 1

    raise ValueError(
        f"Search planner failed to return valid JSON after {config.search_plan_retry_limit} retries."
    )


def extract_valid_search_plans(raw_plans: dict) -> list[SearchPlan]:
    """
    Validates the model output of the search planner.
    Sometimes models return the categories as a JSON string, so we need to handle that as a dict.
    """
    valid_plans = []
    if isinstance(raw_plans["categories"], str):
        search_plans = json.loads(raw_plans["categories"])
    else:
        search_plans = raw_plans["categories"]
    logger.info(f"Search plans: {search_plans}")
    for plan in search_plans:
        logger.info(f"Validating search plan: {plan}")
        try:
            valid_plans.append(SearchPlan.model_validate(plan))
        except Exception:
            logger.warning(f"Invalid search plan: {plan}")
    return valid_plans


def get_search_plan_oai_function() -> dict:
    description = """
Given the state and categories, return a JSON-formatted search plan.
The search plan should be a list of search queries for each category.
"""
    return {
        "type": "function",
        "function": {
            "name": "get_search_plan",
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string"},
                                "queries": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        },
    }
