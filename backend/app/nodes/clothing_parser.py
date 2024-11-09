from typing import Optional
import logging
import requests
import asyncio
import aiohttp

from pydantic import BaseModel, ConfigDict
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.prompts import PromptTemplate
from openai import OpenAI
from langchain_core.language_models import BaseLanguageModel
from bs4 import BeautifulSoup
from langchain_core.messages import AIMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib3.exceptions import ReadTimeoutError

from backend.app.schemas.clothing import ClothingGraphState
from backend.app.schemas.clothing import ClothingItemFunction, ClothingItem
from backend.app.config.config import backend_config
from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from common.utils.vllm import VLLMToolCallClient

logger = logging.getLogger(__name__)


# TODO: Refactor this funciton to use full-BFS once there is a parallel LLM server
class ClothingParserNode(BaseModel, Runnable[ClothingGraphState, ClothingGraphState]):

    name: str = "clothing_parser_node"
    llm: BaseLanguageModel
    fast_llm: BaseLanguageModel
    structured_llm: BaseLanguageModel | OpenAI | VLLMToolCallClient
    stream_handler: AsyncStreamingCallbackHandler
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_llm_and_handler(
        cls,
        llm: BaseLanguageModel,
        fast_llm: BaseLanguageModel,
        structured_llm: BaseLanguageModel,
        stream_handler: AsyncStreamingCallbackHandler,
    ):
        return cls(
            llm=llm,
            fast_llm=fast_llm,
            structured_llm=structured_llm,
            stream_handler=stream_handler,
        )

    def invoke(self, state: ClothingGraphState) -> ClothingGraphState:
        raise NotImplementedError("ClothingParserNode does not support sync invoke")

    async def ainvoke(
        self, state: ClothingGraphState, config: Optional[RunnableConfig] = None
    ) -> ClothingGraphState:
        """
        Process all the search results in serial.
        """
        raw_search_results = state.search_results
        parsed_clothing_items = []
        logger.info(f"raw_search_results = {raw_search_results}")
        for search_result in raw_search_results:
            try:
                processed_items = await self._process_search_result(search_result)
                if processed_items:
                    parsed_clothing_items.extend(processed_items)
            except Exception as e:
                logger.warning(f"Error processing search result: {e}")
                continue

        if not parsed_clothing_items:
            logger.error("No clothing items found")
            raise ValueError("No clothing items found")

        return {"parsed_results": parsed_clothing_items}

    # Process all search results in parallel
    # TODO: Use a parallel LLM server to handle the large number of invocations required for this tool
    # async def ainvoke(
    #     self, state: ClothingGraphState, config: Optional[RunnableConfig] = None
    # ) -> ClothingGraphState:
    #     """
    #     Process all search results in parallel.
    #     """
    #     raw_search_results = state.search_results
    #     parsed_clothing_items = []

    #     try:
    #         # Create tasks but don't start them yet
    #         search_result_tasks = [
    #             self._process_search_result(raw_res) for raw_res in raw_search_results
    #         ]

    #         # Run tasks with asyncio.gather and handle cancellation
    #         completed_results = await asyncio.gather(
    #             *search_result_tasks, return_exceptions=True
    #         )

    #         for result in completed_results:
    #             if isinstance(result, (asyncio.TimeoutError, ReadTimeoutError)):
    #                 logger.warning(f"Timeout processing search result")
    #                 continue
    #             elif isinstance(result, Exception):
    #                 logger.warning(f"Error processing search result: {result}")
    #                 continue
    #             parsed_clothing_items.extend(result)

    #         if not parsed_clothing_items:
    #             logger.error("No clothing items found")
    #             raise ValueError("No clothing items found")

    #         return {"parsed_results": parsed_clothing_items}

    #     except asyncio.CancelledError:
    #         # Properly handle cancellation
    #         logger.info("Received cancellation request")
    #         raise

    async def _process_search_result(self, raw_res: dict) -> list[ClothingItem]:
        """Process a single search result and extract clothing items."""
        url = raw_res["url"]
        logger.info(f"Parsing search result: {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=backend_config.link_click_timeout
                ) as response:
                    content = await response.text()
        except asyncio.TimeoutError:
            logger.warning(f"Timeout processing search result: {url}")
            return []

        chunks = self.split_html(content)

        # TODO: Enable pruning by filtering chunks when connecting to a local LLM server

        # Process chunks in batches of 5 to avoid overwhelming the LLM
        batch_size = backend_config.chunk_batch_size
        items = []

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            batch_items = await asyncio.gather(
                *[self._process_chunk(url, chunk) for chunk in batch]
            )
            # Flatten batch results
            items.extend([item for sublist in batch_items for item in sublist])

        return items

    async def _process_chunk(self, url: str, chunk: str) -> list[ClothingItem]:
        """Process a single HTML chunk and extract clothing items."""
        logger.info(f"Processing chunk: {chunk[:20]}...")
        clicked_links = await self.click_links_and_get_results(url, chunk)
        logger.info(f"Clicked links: {clicked_links}")

        # Process links in batches
        batch_size = backend_config.chunk_batch_size
        items = []

        for i in range(0, len(clicked_links), batch_size):
            batch = clicked_links[i : i + batch_size]
            # Process batch of links in parallel
            batch_items = await asyncio.gather(
                *[self._process_link(clicked_link, url) for clicked_link in batch]
            )
            # Flatten batch results
            items.extend([item for sublist in batch_items for item in sublist])

        return items

    async def _process_link(
        self, clicked_link: str, original_url: str
    ) -> list[ClothingItem]:
        """Process a single link and extract clothing items."""
        logger.info(f"Processing link: {clicked_link}...")
        # TODO: Enable pruning when connecting to a local LLM server
        # is_clothing_product_link = await self.is_clothing_product_link(clicked_link)
        # if not is_clothing_product_link:
        #     logger.info(f"Skipping link: {clicked_link}")
        #     return []

        logger.info(f"Found clothing product link: {clicked_link}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    clicked_link, timeout=backend_config.link_click_timeout
                ) as response:
                    raw_html_content = await response.text()
        except asyncio.TimeoutError:
            logger.warning(f"Timeout processing search result: {clicked_link}")
            return []

        return await self._extract_items_from_html(raw_html_content, original_url)

    async def _extract_items_from_html(
        self, html_content: str, url: str
    ) -> list[ClothingItem]:
        """Extract clothing items from HTML content."""
        logger.info("Extracting items from HTML...")
        # structured_output_llm = self.llm.with_structured_output(ClothingItemList)
        prompt = PromptTemplate(
            input_variables=["url", "content"],
            template=backend_config.clothing_search_result_parser_prompt,
        )
        logger.info("Extracting items from HTML...")
        items = []
        items_streamed = 0

        # Split HTML into chunks and process in parallel
        html_chunks = self.split_html(html_content)
        for chunk in html_chunks:
            if items_streamed >= backend_config.max_clothing_items_to_stream:
                break
            # TODO: Enable pruning by filtering chunks when connecting to a parallel local LLM server
            # if not await self.contains_clothing_item_info_or_links(chunk):
            #     continue
            try:
                raw_res = await self.structured_llm.ainvoke_with_tools(
                    prompt.format(url=url, content=chunk),
                    tools=[self.get_clothing_item_oai_function()],
                )
                logger.info(f"Raw Extracted item: {raw_res}")
                extracted_item = ClothingItem.model_validate(raw_res)
            except Exception as e:
                logger.exception("Error extracting items from chunk")
                continue
            items.append(extracted_item)

            # Only stream the clothing item if all fields are non-null
            if all(
                getattr(extracted_item, field) is not None
                for field in extracted_item.model_fields
            ):
                await self.stream_handler.on_extracted_item(extracted_item)
                items_streamed += 1
        return items

    async def is_clothing_product_link(self, url: str) -> bool:
        prompt = PromptTemplate(
            input_variables=["url"],
            template=backend_config.is_clothing_product_link_prompt,
        )
        extract_prompt = prompt.format(url=url)
        # TODO: Add batching to speed up processing
        raw_res = AIMessage.model_validate(
            await self.fast_llm.ainvoke(extract_prompt)
        ).content
        return "true" in raw_res.lower()

    async def contains_clothing_item_info_or_links(self, html_chunk: str) -> bool:
        """
        Returns True if the HTML chunk is about a clothing item
        or links that are promising for finding clothing items, False otherwise.
        """
        logger.info(f"Checking if chunk contains clothing info: {html_chunk[:20]}...")
        prompt = PromptTemplate(
            input_variables=["html"],
            template=backend_config.html_contains_clothing_info_prompt,
        )
        extract_prompt = prompt.format(html=html_chunk)
        raw_res = AIMessage.model_validate(
            await self.fast_llm.ainvoke(extract_prompt)
        ).content
        return (
            "true" in raw_res.lower()
        )  # TODO: Consider structured output in the future

    @staticmethod
    async def click_links_and_get_results(parent_url: str, raw_html: str) -> list[str]:
        """
        Extracts all links from the raw HTML string.

        Args:
            raw_html: Raw HTML string to parse

        Returns:
            List of URLs found in the HTML
        """
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            anchors = soup.find_all("a")
        except Exception as e:
            logger.exception("Error parsing HTML")
            return []
        links = []
        for anchor in anchors:
            try:
                # Get the href attribute
                href = anchor.get("href")

                if href and not href.startswith("#"):  # Skip anchor links
                    if not href.lower().startswith(("http://", "https://")):
                        # Relative URL - join with parent URL
                        href = urljoin(parent_url, href)
                    links.append(href)

            except Exception as e:
                logger.exception("Error processing link")
                continue

        return links

    @staticmethod
    def split_html(html: str) -> list[str]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=backend_config.chunk_size,
            chunk_overlap=backend_config.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        return text_splitter.split_text(html)

    @staticmethod
    def get_clothing_item_oai_function() -> dict:
        description = """
Given the text, extract one clothing item mentioned.
Make sure to extract the full image link in the <img> src attribute.
"""
        return {
            "type": "function",
            "function": {
                "name": "extract_clothing_item",
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "price": {"type": "number"},
                        "image_url": {"type": "string"},
                        "link": {"type": "string"},
                    },
                    "required": ["name", "price", "image_url", "link"],
                },
            },
        }
