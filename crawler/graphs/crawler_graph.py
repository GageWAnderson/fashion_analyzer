from functools import partial

from pydantic import BaseModel
from langgraph.graph import StateGraph
from langgraph.graph import START, END

from crawler.schemas.state import WebCrawlerState
from crawler.tools.search_tool import search_tool
from crawler.tools.search_rephraser_tool import search_rephraser_tool
from crawler.tools.search_planner_tool import search_planner_tool
from crawler.tools.search_done_tool import search_done_tool
from crawler.db.vector_store import ChromaVectorStore
from crawler.schemas.config import CrawlerConfig


class CrawlerGraph(BaseModel):
    graph: StateGraph

    @classmethod
    def from_config(cls, config: CrawlerConfig) -> "CrawlerGraph":
        graph_builder = StateGraph(WebCrawlerState)

        vector_store = ChromaVectorStore.from_config(config)

        # TODO: Refactor tools to be LangChain Tool objects that have a .from_config method
        graph_builder.add_node("search_planner", partial(search_planner_tool, config))
        graph_builder.add_node("search_tool", partial(search_tool, vector_store))
        graph_builder.add_node(
            "search_rephraser", partial(search_rephraser_tool, config)
        )

        graph_builder.add_edge(START, "search_planner")
        graph_builder.add_edge("search_planner", "search_tool")
        graph_builder.add_conditional_edges(
            "search_tool",
            search_done_tool,
            path_map={
                "true": END,
                "false": "search_planner",
                "rephrase": "search_rephraser",
            },
        )
        graph_builder.add_edge("search_rephraser", "search_planner")

        graph = graph_builder.compile()
        return cls(graph=graph)
