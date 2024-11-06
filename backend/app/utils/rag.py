import logging

from langchain.schema import AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.language_models import BaseLanguageModel

from backend.app.config.config import backend_config
from common.schemas.vector_metadata import VectorMetadata

logger = logging.getLogger(__name__)


async def summarize_docs(
    user_question: str,
    metadatas: list[VectorMetadata],
    llm: BaseLanguageModel,
) -> AIMessage:
    prompt = PromptTemplate(
        input_variables=["question", "docs", "sources", "image_links"],
        template=backend_config.summarize_docs_prompt,
    )
    summarize_prompt = prompt.format(
        question=user_question,
        sources="\n".join(get_source_urls(metadatas)),
        image_links="\n".join(
            get_image_urls(metadatas)[: backend_config.max_images_to_display]
        ),  # TODO: Filter down to a smaller number of images
    )
    logger.info(f"Summarize prompt: {summarize_prompt}")

    return AIMessage.model_validate(await llm.ainvoke(summarize_prompt))


def get_metadatas(docs: list[Document]) -> list[VectorMetadata]:
    return [VectorMetadata.model_validate(doc.metadata) for doc in docs]


def get_source_urls(metadatas: list[VectorMetadata]) -> list[str]:
    return [metadata.url for metadata in metadatas if metadata.url]


def get_image_urls(source_metadatas: list[VectorMetadata]) -> list[str]:
    # TODO: Return only the most relevant image URLs
    try:
        image_urls = []
        for source_metadata in source_metadatas:
            if source_metadata.image_metadata:
                for image_metadata in source_metadata.image_metadata:
                    image_urls.append(image_metadata["url"])
        return image_urls
    except Exception:
        logger.exception("Error getting image URLs")
        logger.warning("No image URLs found for query")
        return ["No image URLs found"]
