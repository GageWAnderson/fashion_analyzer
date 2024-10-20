import uuid
import requests
import logging
from datetime import datetime
import base64
from io import BytesIO

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


async def save_tavily_res_to_vector_db(
    query: str, tavily_res: AIMessage, vector_store: VectorStore
) -> None:
    res_content = tavily_res.content[0][
        "content"
    ]  # TODO: Find a better way to break the content down into finer chunks
    # TODO: Break down the content into chunks with unstructured.io
    res_url = tavily_res.content[0]["url"]
    logger.debug(f"Query: {query}")
    logger.debug(f"Searching URL: {res_url}")

    image_metadata = await extract_tavily_res_images(res_url)

    metadata = VectorMetadata(
        query=query,
        url=res_url,
        image_metadata=image_metadata,
        timestamp=datetime.now().isoformat(),
        source_type="web_page",
        content_summary=await summarize_content(res_content),
        relevance_score=0.85,  # TODO: Generate a relevance score at crawl time with the LLM
    ).model_dump(mode="json")
    logger.debug(f"Metadata: {metadata}")

    # TODO: Should we embed by page content or by summary?
    # text_chunks = partition_web_page(res_url)
    doc = Document(
        page_content=res_content,
        metadata=metadata,
    )

    vector_store.add_documents(documents=[doc])


async def extract_tavily_res_images(url: str) -> list[ImageMetadata]:
    """
    Extracts all images and other media from the Tavily search results and stores them in Minio.
    Returns presigned URLs to use in the metadata of the document the images etc. were extracted from.
    """
    try:
        image_urls = await scrape_images_from_page(url)
    except Exception:
        logger.exception("Error partitioning web page:")
        logger.warning(
            f"No images found for URL: {url}, returning empty image metadata list"
        )
        return []

    res: list[ImageMetadata] = []
    for image_url in image_urls:
        # TODO: Replace requests with httpx
        image_response = PILImage.open(requests.get(image_url, stream=True).raw)
        minio_url = await minio_put_object(image_response)
        res.append(
            ImageMetadata(url=minio_url, summary=await summarize_image(image_response))
        )
    return res


def summarize_image(image: PILImage.Image) -> str:
    """
    Uses a powerful LLM to generate a 1-sentence summary of an image
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
    return llm.ainvoke(messages)


async def summarize_content(content: str) -> str:
    llm = get_llm_from_config(config)
    summarize_prompt = PromptTemplate(
        template=config.summarize_content_prompt, input_variables=["content"]
    )
    return llm.ainvoke(summarize_prompt.format(content=content)).content


async def scrape_images_from_page(url: str) -> list[str]:
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
