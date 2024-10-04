import json
import uuid
import logging
from datetime import datetime

from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.messages import AIMessage
from langchain_community.vectorstores import VectorStore
from unstructured.documents.elements import Element, Image

from crawler.utils.minio import minio_put_object
from crawler.utils.unstructured_io import partition_web_page
from crawler.schemas.vector_metadata import VectorMetadata

logger = logging.getLogger(__name__)


def save_tavily_res_to_vector_db(
    tavily_res: AIMessage, vector_store: VectorStore
) -> None:
    chunk_id = str(uuid.uuid4())
    search_msg = tavily_res.content[0][
        "content"
    ]  # TODO: Find a better way to break the content down into finer chunks
    search_url = tavily_res.content[0]["url"]
    doc = Document(
        page_content=search_msg,
        metadata=VectorMetadata(
            query=search_msg,
            url=search_url,
            image_urls=extract_tavily_res_content(search_url),
            chunk_id=chunk_id,
            timestamp=datetime.now().isoformat(),
            source_type="web_page",
            content_summary="Overview of spring/summer fashion trends for 2023",
            relevance_score=0.85,
        ).model_dump(),
        id=chunk_id,
    )

    vector_store.add_documents(documents=[doc], ids=[chunk_id])


def extract_tavily_res_content(url: str) -> str:
    """
    Extracts all images and other media from the Tavily search results and stores them in Minio.
    Returns a presigned URL to use in the metadata of the document the images etc. were extracted from.
    """
    elements = partition_web_page(url)
    res = []
    for element in elements:
        if isinstance(element, Image):
            response = minio_put_object(element.get_content(), element.mime_type)
            res.append(response.url)
        # TODO: handle other element types
    return json.dumps(res)
