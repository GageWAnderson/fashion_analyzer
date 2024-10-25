import logging

from langchain_core.prompts import PromptTemplate

from crawler.config.config import CrawlerConfig
from crawler.schemas.state import WebCrawlerState
from crawler.schemas.search import SearchPlans
from common.utils.json import extract_json_from_markdown
from common.utils.time import get_current_year_and_month
from common.utils.llm import get_llm_from_config

logger = logging.getLogger(__name__)


# TODO Refactor into a LangChain tool with a from_config method
def search_planner_tool(config: CrawlerConfig, state: WebCrawlerState):
    retries = 0
    search_planner_prompt_template = PromptTemplate.from_template(
        config.search_planner_prompt
    )
    llm = get_llm_from_config(config)

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
        raw_search_plan = llm.invoke(input=search_planner_prompt(state))
        try:
            extracted_json = extract_json_from_markdown(raw_search_plan.content)
            logger.debug(f"Extracted JSON = {extracted_json}")
            search_plan = SearchPlans.model_validate_json(extracted_json)
            return {"messages": state["messages"], "search_plans": search_plan}
        except Exception:
            logger.exception("Retrying search plan extraction")
            retries += 1

    raise ValueError(
        f"Search planner failed to return valid JSON after {config.search_plan_retry_limit} retries."
    )
