import logging

from langchain_core.messages import AIMessage
from langgraph.graph.message import add_messages
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.vectorstores import VectorStore

from crawler.schemas.state import WebCrawlerState
from crawler.schemas.search import increment_search_iterations
from crawler.utils.search_results_processor import SearchResultProcessor

logger = logging.getLogger(__name__)


# TODO: Improve model consistency at outputting JSON search plans
async def search_tool(vector_store: VectorStore, state: WebCrawlerState):
    logger.debug(f"State at start of search_tool: {state}")
    search_plan = state[
        "search_plans"
    ]  # Assume the search planner always goes to the search tool
    search_result_processor = SearchResultProcessor.from_vector_store(vector_store)
    for plan in search_plan.plans:
        logger.debug(f"Search plan: {plan}")
        tavily_search = TavilySearchResults()
        for query in plan.queries:
            res = AIMessage(
                content=tavily_search.invoke({"query": query})
            )  # TODO: make res more readable
            if "HTTPError" in res.content:
                raise ValueError(f"HTTP exception in calling Tavily API: {res}")
            await search_result_processor.process_and_save_result(query, res)
            add_messages(state["messages"], res)

    return {
        "messages": state["messages"],
        "num_search_iterations": increment_search_iterations(
            state["num_search_iterations"], 1
        ),
    }
