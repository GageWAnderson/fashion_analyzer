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

    # TODO: Clean up the nested for loops here
    async def ainvoke(
        self, state: ClothingGraphState, config: Optional[RunnableConfig] = None
    ) -> ClothingGraphState:
        raw_search_results = state.search_results
        parsed_clothing_items = []
        # for raw_res in raw_search_results:
        #     url = raw_res["url"]
        #     logger.info(f"Parsing search result: {url}")
        #     content = requests.get(url).text
        #     for chunk in self.split_html(content):
        #         clicked_links = await self.click_links_and_get_results(url, chunk)
        #         for clicked_link in clicked_links:
        #             if self.is_clothing_product_link(clicked_link):
        #                 logger.debug(f"Found clothing product link: {clicked_link}")
        #                 try:
        #                     raw_html_content = requests.get(clicked_link).text
        #                     for split_html_content in self.split_html(raw_html_content):
        #                         if not self.contains_clothing_item_info_or_links(
        #                             split_html_content
        #                         ):
        #                             logger.info("Skipping chunk")
        #                             continue
        #                         result = await self.parse_search_result(
        #                             split_html_content
        #                         )
        #                         logger.info(f"Parsed result: {result}")
        #                         for parsed_clothing_item in result:
        #                             logger.info(
        #                                 f"Streaming Extracted item: {parsed_clothing_item}"
        #                             )
        #                             await self.stream_handler.on_extracted_item(
        #                                 parsed_clothing_item
        #                             )
        #                             parsed_clothing_items.append(parsed_clothing_item)
        #                 except Exception as e:
        #                     logger.exception("Error parsing chunk")
        #                     continue
        return {"parsed_results": parsed_clothing_items}

    async def parse_search_result(self, raw_html: str) -> list[ClothingItem]:
        try:
            return self.result_extractor(raw_html).clothing_items
        except Exception as e:
            logger.exception(f"Error parsing results")
            return []

    def result_extractor(self, raw_results: str) -> ClothingItemList:
        structured_output_llm = self.llm.with_structured_output(ClothingItemList)

        for attempt in range(backend_config.max_retries):
            try:
                raw_res = structured_output_llm.invoke(raw_results)
                logger.info(f"Raw res: {raw_res}")
                return ClothingItemList.model_validate(raw_res)
            except Exception as e:
                if attempt == backend_config.max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")

    def is_clothing_product_link(self, url: str) -> bool:
        prompt = PromptTemplate(
            input_variables=["url"],
            template=backend_config.is_clothing_product_link_prompt,
        )
        extract_prompt = prompt.format(url=url)
        raw_res = AIMessage.model_validate(self.fast_llm.invoke(extract_prompt)).content
        return "true" in raw_res.lower()

    def contains_clothing_item_info_or_links(self, html_chunk: str) -> bool:
        """
        Returns True if the HTML chunk is about a clothing item
        or links that are promising for finding clothing items, False otherwise.
        """
        prompt = PromptTemplate(
            input_variables=["html"],
            template=backend_config.html_contains_clothing_info_prompt,
        )
        extract_prompt = prompt.format(html=html_chunk)
        raw_res = AIMessage.model_validate(self.fast_llm.invoke(extract_prompt)).content
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
