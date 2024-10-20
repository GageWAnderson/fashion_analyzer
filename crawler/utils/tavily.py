import uuid
import requests
import logging
from datetime import datetime
import base64
from io import BytesIO

from PIL import Image as PILImage, ImageFile
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_community.vectorstores import VectorStore
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage
from unstructured.documents.elements import Image

from common.utils.llm import get_llm_from_config
from common.utils.minio import minio_put_object
from common.utils.unstructured_io import partition_web_page
from common.schemas.vector_metadata import VectorMetadata
from common.schemas.image_metadata import ImageMetadata
from crawler.config.config import config

logger = logging.getLogger(__name__)


def save_tavily_res_to_vector_db(
    tavily_res: AIMessage, vector_store: VectorStore
) -> None:
    chunk_id = str(uuid.uuid4())
    search_msg = tavily_res.content[0][
        "content"
    ]  # TODO: Find a better way to break the content down into finer chunks
    search_url = tavily_res.content[0]["url"]
    logger.debug(f"Search message: {search_msg}")
    logger.debug(f"Searching URL: {search_url}")

    image_metadata = extract_tavily_res_content(search_url)
    logger.debug(f"Image Metadata: {image_metadata}")

    metadata = VectorMetadata(
        query=search_msg,
        url=search_url,
        image_metadata=image_metadata,
        chunk_id=chunk_id,
        timestamp=datetime.now().isoformat(),
        source_type="web_page",
        content_summary="",  # TODO: Generate a summary at crawl time with the LLM
        relevance_score=0.85,  # TODO: Generate a relevance score at crawl time with the LLM
    ).model_dump(mode="json")
    logger.debug(f"Metadata: {metadata}")

    doc = Document(
        page_content=search_msg,
        metadata=metadata,
        id=chunk_id,
    )

    vector_store.add_documents(documents=[doc], ids=[chunk_id])


def extract_tavily_res_content(url: str) -> list[ImageMetadata]:
    """
    Extracts all images and other media from the Tavily search results and stores them in Minio.
    Returns a presigned URL to use in the metadata of the document the images etc. were extracted from.
    """
    try:
        # TODO: Is there a better way to scrape images from the web page?
        elements = partition_web_page(url)
    except Exception:
        logger.exception("Error partitioning web page:")
        return []
    res: list[ImageMetadata] = []
    for element in elements:
        if isinstance(element, Image):
            response = minio_put_object(element.get_content(), element.mime_type)
            # TODO: Replace requests with httpx
            image_response = PILImage.open(requests.get(response.url, stream=True).raw)
            res.append(
                ImageMetadata(url=response.url, summary=summarize_image(image_response))
            )
        # TODO: handle other element types
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
    response = llm.generate([messages])
    return response.generations[0][0].text
