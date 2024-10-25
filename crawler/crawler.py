import logging
import asyncio

from langchain_core.messages import HumanMessage

from crawler.graphs.crawler_graph import CrawlerGraph
from crawler.config.config import config, CrawlerConfig
from crawler.config.logging_config import setup_logging

# Set up logging
root_logger = setup_logging(config)

logger = logging.getLogger(__name__)


def main():
    try:
        logger.info("Starting crawl process")
        logger.debug(f"Config: {config}")
        asyncio.run(crawl())
        logger.info("Crawl process completed")
    except Exception:
        logger.exception("An error occurred during the crawl process")


async def crawl():
    graph = await CrawlerGraph.from_config(config)

    init_msg = [HumanMessage(content=config.init_message)]
    logger.debug(f"Initial message: {config.init_message}")
    async for event in graph.graph.astream(
        {"messages": init_msg, "search_categories": get_init_search_categories(config)}
    ):
        for value in event.values():
            # TODO: Handle connection refused errors and recover
            assistant_message = value["messages"][-1].content
            logger.info(f"Assistant: {assistant_message}")


def get_init_search_categories(config: CrawlerConfig) -> list[str]:
    if config.search_gender == "men":
        return config.men_fashion_categories
    else:
        return config.women_fashion_categories
