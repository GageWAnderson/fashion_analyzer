import logging

from langchain_core.messages import AIMessage
from langgraph.graph.message import add_messages
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.vectorstores import VectorStore

from crawler.schemas.state import WebCrawlerState
from crawler.schemas.search import increment_search_iterations
from crawler.utils.tavily import save_tavily_res_to_vector_db

logger = logging.getLogger(__name__)


# TODO: Improve model consistency at outputting JSON search plans
def search_tool(vector_store: VectorStore, state: WebCrawlerState):
    logger.debug(f"State at start of search_tool: {state}")
    search_plan = state[
        "search_plans"
    ]  # Assume the search planner always goes to the search tool

    for plan in search_plan.plans:
        logger.debug(f"Search plan: {plan}")
        tavily_search = TavilySearchResults()
        for query in plan.queries:
            res = AIMessage(
                content=tavily_search.invoke({"query": query})
            )  # TODO: make res more readable
            if "HTTPError" in res.content:
                raise ValueError(f"HTTP exception in calling Tavily API: {res}")
            save_tavily_res_to_vector_db(res, vector_store)
            add_messages(state["messages"], res)

    return {
        "messages": state["messages"],
        "num_search_iterations": increment_search_iterations(
            state["num_search_iterations"], 1
        ),
    }
