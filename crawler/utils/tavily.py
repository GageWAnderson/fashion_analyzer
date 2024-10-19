import uuid
import logging
from datetime import datetime

from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_community.vectorstores import VectorStore
from unstructured.documents.elements import Image

from common.utils.minio import minio_put_object
from common.utils.unstructured_io import partition_web_page
from common.schemas.vector_metadata import VectorMetadata

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

    image_urls = extract_tavily_res_content(search_url)
    logger.debug(f"Image URLs: {image_urls}")

    metadata = VectorMetadata(
        query=search_msg,
        url=search_url,
        image_urls=image_urls,
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


def extract_tavily_res_content(url: str) -> str:
    """
    Extracts all images and other media from the Tavily search results and stores them in Minio.
    Returns a presigned URL to use in the metadata of the document the images etc. were extracted from.
    """
    try:
        # TODO: Is there a better way to scrape images from the web page?
        elements = partition_web_page(url)
    except Exception:
        logger.exception("Error partitioning web page:")
        return ""
    res = []
    for element in elements:
        if isinstance(element, Image):
            response = minio_put_object(element.get_content(), element.mime_type)
            res.append(response.url)
        # TODO: handle other element types
    return ",".join(res)
