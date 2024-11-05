from typing import Optional
import logging
import requests

from pydantic import BaseModel, ConfigDict
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from bs4 import BeautifulSoup
from langchain_core.messages import AIMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from backend.app.schemas.clothing import ClothingGraphState
from backend.app.schemas.clothing import ClothingItemList, ClothingItem
from backend.app.config.config import backend_config
from backend.app.utils.streaming import AsyncStreamingCallbackHandler

logger = logging.getLogger(__name__)


class ClothingParserNode(BaseModel, Runnable[ClothingGraphState, ClothingGraphState]):

    name: str = "clothing_parser_node"
    llm: BaseLanguageModel
    fast_llm: BaseLanguageModel
    stream_handler: AsyncStreamingCallbackHandler
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_llm_and_handler(
        cls,
        llm: BaseLanguageModel,
        fast_llm: BaseLanguageModel,
        stream_handler: AsyncStreamingCallbackHandler,
    ):
        return cls(llm=llm, fast_llm=fast_llm, stream_handler=stream_handler)

    def invoke(self, state: ClothingGraphState) -> ClothingGraphState:
        raise NotImplementedError("ClothingParserNode does not support sync invoke")

    async def ainvoke(
        self, state: ClothingGraphState, config: Optional[RunnableConfig] = None
    ) -> ClothingGraphState:
        raw_search_results = state.search_results
        parsed_clothing_items = []

        for raw_res in raw_search_results:
            items = await self._process_search_result(raw_res)
            parsed_clothing_items.extend(items)

        return {"parsed_results": parsed_clothing_items}

    async def _process_search_result(self, raw_res: dict) -> list[ClothingItem]:
        """Process a single search result and extract clothing items."""
        url = raw_res["url"]
        logger.info(f"Parsing search result: {url}")
        items = []

        content = requests.get(url).text
        for chunk in self.split_html(content):
            chunk_items = await self._process_chunk(url, chunk)
            items.extend(chunk_items)

        return items

    async def _process_chunk(self, url: str, chunk: str) -> list[ClothingItem]:
        """Process a single HTML chunk and extract clothing items."""
        items = []
        clicked_links = await self.click_links_and_get_results(url, chunk)

        for clicked_link in clicked_links:
            link_items = await self._process_link(clicked_link, url)
            items.extend(link_items)

        return items

    async def _process_link(
        self, clicked_link: str, original_url: str
    ) -> list[ClothingItem]:
        """Process a single link and extract clothing items."""
        is_clothing_product_link = await self.is_clothing_product_link(clicked_link)
        if not is_clothing_product_link:
            return []

        logger.debug(f"Found clothing product link: {clicked_link}")
        items = []

        try:
            raw_html_content = requests.get(clicked_link).text
            items = await self._extract_items_from_html(raw_html_content, original_url)
        except Exception as e:
            logger.exception("Error parsing chunk")

        return items

    async def _extract_items_from_html(
        self, html_content: str, url: str
    ) -> list[ClothingItem]:
        """Extract clothing items from HTML content."""
        items = []
        items_streamed = 0

        for split_html_content in self.split_html(html_content):
            contains_clothing_item_info = (
                await self.contains_clothing_item_info_or_links(split_html_content)
            )
            if not contains_clothing_item_info:
                logger.info("Skipping chunk")
                continue

            result = await self.parse_search_result(
                url=url, raw_html=split_html_content
            )
            logger.info(f"Parsed result: {result}")

            for item in result:
                items.append(item)
                # Only stream if all fields have values
                # if (
                #     items_streamed < backend_config.max_clothing_items_to_stream
                #     and all(
                #         getattr(item, field) is not None for field in item.model_fields
                #     )
                # ):
                logger.info(f"Streaming Extracted item: {item}")
                await self.stream_handler.on_extracted_item(item)
                items_streamed += 1

        return items

    async def parse_search_result(self, url, raw_html: str) -> list[ClothingItem]:
        try:
            items = await self.result_extractor(url, raw_html)
            return items.clothing_items
        except Exception as e:
            logger.exception(f"Error parsing results")
            return []

    async def result_extractor(self, url: str, raw_results: str) -> ClothingItemList:
        structured_output_llm = self.llm.with_structured_output(ClothingItemList)

        for attempt in range(backend_config.max_retries):
            try:
                prompt = PromptTemplate(
                    input_variables=["url", "content"],
                    template=backend_config.clothing_search_result_parser_prompt,
                )
                raw_res = await structured_output_llm.ainvoke(
                    prompt.format(url=url, content=raw_results)
                )
                logger.info(f"Raw res: {raw_res}")
                return ClothingItemList.model_validate(raw_res)
            except Exception as e:
                if attempt == backend_config.max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")

    async def is_clothing_product_link(self, url: str) -> bool:
        prompt = PromptTemplate(
            input_variables=["url"],
            template=backend_config.is_clothing_product_link_prompt,
        )
        extract_prompt = prompt.format(url=url)
        raw_res = AIMessage.model_validate(
            await self.fast_llm.ainvoke(extract_prompt)
        ).content
        return "true" in raw_res.lower()

    async def contains_clothing_item_info_or_links(self, html_chunk: str) -> bool:
        """
        Returns True if the HTML chunk is about a clothing item
        or links that are promising for finding clothing items, False otherwise.
        """
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
