import traceback

from langchain_core.messages import HumanMessage

from crawler.graphs.crawler_graph import CrawlerGraph
from crawler.schemas.config import config
from crawler.config.logging_config import setup_logging

# Set up logging
logger = setup_logging()


def crawl():
    graph = CrawlerGraph.from_config(config).graph

    init_msg = [HumanMessage(content=config.init_message)]
    logger.info(f"Initial message: {config.init_message}")
    for event in graph.stream({"messages": init_msg}):
        for value in event.values():
            assistant_message = value["messages"][-1].content
            logger.info(f"Assistant: {assistant_message}")

    logger.info("Crawl process completed")


def main():
    try:
        logger.info("Starting crawl process")
        logger.info(f"Config: {config}")
        crawl()
        logger.info("Crawl process completed")
    except Exception as e:
        logger.error(f"An error occurred during the crawl process: {str(e)}")
        logger.error(traceback.format_exc())
