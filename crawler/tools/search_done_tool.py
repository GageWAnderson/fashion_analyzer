import logging

from langchain_core.messages import AIMessage

from crawler.config.config import CrawlerConfig
from crawler.schemas.state import WebCrawlerState
from common.utils.llm import get_llm_from_config

from langchain_core.prompts import PromptTemplate
from common.utils.time import get_current_year_and_month


logger = logging.getLogger(__name__)


def search_done_tool(config: CrawlerConfig, state: WebCrawlerState) -> bool:
    if state["num_search_iterations"] < config.num_search_iterations:
        return (
            "rephrase"  # Rephrase the queries to search a greater variety of websites
        )

    # TODO: Fine-tune an LLM to check if a search is complete
    is_done_prompt_template = PromptTemplate.from_template(config.is_done_prompt)
    llm = get_llm_from_config(config)

    def is_done_prompt(state: WebCrawlerState) -> PromptTemplate:
        current_year, current_month = get_current_year_and_month()
        return is_done_prompt_template.format(
            state=state,
            current_year=current_year,
            current_month=current_month,
            categories=",\n".join(state["search_categories"]),
        )

    try:
        res = AIMessage.model_validate(llm.invoke(is_done_prompt(state))).content
    except Exception as e:
        logger.warning("LLM failed to decide if search was complete, stopping search.")
        logger.exception(f"There was an exception making the search done prompt: {e}")
        return "true"

    if "true" in res.lower():
        logger.debug("AGENT DONE")
        return "true"
    else:
        logger.debug("AGENT NOT DONE, STARTING NEXT SEARCH")
        return "false"
