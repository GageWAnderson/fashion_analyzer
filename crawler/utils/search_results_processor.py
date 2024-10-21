import requests
import logging
from datetime import datetime
import base64
from io import BytesIO

from pydantic import BaseModel, ConfigDict
from PIL import Image as PILImage
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.vectorstores import VectorStore
from unstructured.documents.elements import Image
from playwright.async_api import async_playwright

from common.utils.llm import get_llm_from_config
from common.utils.minio import minio_put_object
from common.utils.unstructured_io import partition_web_page
from langchain_core.prompts import PromptTemplate
from common.schemas.vector_metadata import VectorMetadata
from common.schemas.image_metadata import ImageMetadata
from crawler.config.config import config

logger = logging.getLogger(__name__)


class SearchResultProcessor(BaseModel):
    vector_store: VectorStore
    model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_vector_store(cls, vector_store: VectorStore):
        """
        Creates a SearchResultProcessor instance from a VectorStore.

        Args:
            vector_store (VectorStore): The vector store to use for processing search results.

        Returns:
            SearchResultProcessor: An instance of SearchResultProcessor.
        """
        return cls(vector_store=vector_store)

    async def process_and_save_result(self, query: str, tavily_res: AIMessage) -> None:
        """
        Processes and saves a search result from Tavily.

        Args:
            query (str): The search query.
            tavily_res (AIMessage): The search result from Tavily.

        Returns:
            None
        """
        res_content = tavily_res.content[0][
            "content"
        ]  # TODO: Find a better way to break the content down into finer chunks
        # TODO: Break down the content into chunks with unstructured.io
        res_url = tavily_res.content[0]["url"]
        logger.info(f"Query: {query}")
        logger.info(f"Searching URL: {res_url}")

        image_metadata = await self.extract_tavily_res_images(res_url)

        metadata = VectorMetadata(
            query=query,
            url=res_url,
            image_metadata=image_metadata,
            timestamp=datetime.now().isoformat(),
            source_type="web_page",
            content_summary=await self.summarize_content(res_content),
            relevance_score=0.85,  # TODO: Generate a relevance score at crawl time with the LLM
        ).model_dump(mode="json")
        logger.info(f"Metadata: {metadata}")

        # TODO: Should we embed by page content or by summary?
        # text_chunks = partition_web_page(res_url)
        doc = Document(
            page_content=res_content,
            metadata=metadata,
        )
        logger.info(f"Adding document to vector store: {doc}")
        self.vector_store.add_documents(documents=[doc])

    async def extract_tavily_res_images(self, url: str) -> list[ImageMetadata]:
        """
        Extracts all images and other media from the Tavily search results and stores them in Minio.
        Returns presigned URLs to use in the metadata of the document the images etc. were extracted from.

        Args:
            url (str): The URL of the web page to extract images from.

        Returns:
            list[ImageMetadata]: A list of ImageMetadata objects containing image URLs and summaries.
        """
        try:
            image_urls = await self.scrape_images_from_page(url)
        except Exception:
            logger.exception("Error partitioning web page:")
            logger.warning(
                f"No images found for URL: {url}, returning empty image metadata list"
            )
            return []

        res: list[ImageMetadata] = []
        for image_url in image_urls:
            try:
                image = PILImage.open(requests.get(image_url, stream=True).raw)
            except Exception:
                logger.exception(f"Error opening image: {image_url}")
                logger.warning(f"Skipping image: {image_url}")
                continue
            content_type = (
                "image/jpeg"
                if image.format.lower() == "jpeg" or image.format.lower() == "jpg"
                else "image/png"
            )
            # Save the image to a BytesIO object to preserve format and metadata
            image_bytes_io = BytesIO()
            image.save(image_bytes_io, format=image.format)
            image_bytes_io.seek(0)
            minio_response = minio_put_object(image_bytes_io, content_type)
            res.append(
                ImageMetadata(
                    url=minio_response.url, summary=await self.summarize_image(image)
                )
            )
        return res

    async def summarize_image(self, image: PILImage.Image) -> str:
        """
        Uses a powerful LLM to generate a 1-sentence summary of an image.

        Args:
            image (PILImage.Image): The image to summarize.

        Returns:
            str: A one-sentence summary of the image.
        """
        llm = get_llm_from_config(config, llm=config.vision_llm)
        # Encode the image as base64
        buffered = BytesIO()
        image_format = image.format.upper()
        image.save(buffered, format=image_format)

        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_url_prefix = f"data:image/{image_format.lower()};base64,"

        messages = [
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": config.summarize_image_prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"{image_url_prefix}{image_base64}"},
                    },
                ],
            )
        ]
        return AIMessage.model_validate(await llm.ainvoke(messages)).content

    async def summarize_content(self, content: str) -> str:
        """
        Summarizes the given content using an LLM.

        Args:
            content (str): The content to summarize.

        Returns:
            str: A summary of the content.
        """
        llm = get_llm_from_config(config)
        summarize_prompt = PromptTemplate(
            template=config.summarize_content_prompt, input_variables=["content"]
        )
        return AIMessage.model_validate(
            await llm.ainvoke(summarize_prompt.format(content=content))
        ).content

    async def scrape_images_from_page(self, url: str) -> list[str]:
        """
        Scrapes all image URLs from a given web page.

        Args:
            url (str): The URL of the web page to scrape.

        Returns:
            list[str]: A list of image URLs found on the page.
        """
        image_urls = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)

            # Scrape all img tags and get their 'src' attributes
            images = await page.query_selector_all("img")
            for img in images:
                src = await img.get_attribute("src")
                if src and src.startswith("http"):
                    image_urls.append(src)

            await browser.close()

        return image_urls
