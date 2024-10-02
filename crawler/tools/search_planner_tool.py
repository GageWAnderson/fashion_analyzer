import traceback

from langchain_core.prompts import PromptTemplate

from crawler.schemas.config import CrawlerConfig
from crawler.schemas.state import WebCrawlerState
from crawler.schemas.search import SearchPlans
from crawler.utils.json import extract_json_from_markdown
from crawler.utils.time import get_current_year_and_month
from crawler.utils.llm import get_llm


# TODO Refactor into a LangChain tool with a from_config method
def search_planner_tool(config: CrawlerConfig, state: WebCrawlerState):
    retries = 0
    search_planner_prompt_template = PromptTemplate.from_template(
        config.search_planner_prompt
    )
    llm = get_llm(config.llm)

    def search_planner_prompt(state: WebCrawlerState) -> PromptTemplate:
        current_year, current_month = get_current_year_and_month()
        return search_planner_prompt_template.format(
            state=state,
            current_year=current_year,
            current_month=current_month,
            categories=",\n".join(state["search_categories"]),
        )

    while retries < config.search_plan_retry_limit:
        raw_search_plan = llm.invoke(input=search_planner_prompt(state))
        try:
            extracted_json = extract_json_from_markdown(raw_search_plan.content)
            print(f"Extracted JSON = {extracted_json}")
            search_plan = SearchPlans.model_validate_json(extracted_json)
            return {"messages": state["messages"], "search_plans": search_plan}
        except Exception as e:
            print(f"Retrying search plan extraction: {e}")
            print(traceback.print_exc())
            retries += 1

    raise ValueError(
        f"Search planner failed to return valid JSON after {config.search_plan_retry_limit} retries."
    )
