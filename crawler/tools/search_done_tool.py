import logging

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

    res = llm.invoke(input=is_done_prompt(state)).content
    if "true" in res.lower():
        logger.debug("AGENT DONE")
        return "true"
    elif "false" in res.lower():
        logger.debug("AGENT NOT DONE, STARTING NEXT SEARCH")
        return "false"
    else:
        logger.debug(f"{res}")
        raise ValueError("AI failed to decide if search was complete.")
