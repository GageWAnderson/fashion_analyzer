from typing import Optional
import logging
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.language_models import BaseLanguageModel
from langchain.schema import AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

from backend.app.schemas.rag import RagState
from backend.app.schemas.agent_state import AgentState
from backend.app.config.config import backend_config
from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from common.utils.llm import get_llm_from_config
from common.schemas.vector_metadata import VectorMetadata

logger = logging.getLogger(__name__)


class SummarizeDocsNode(Runnable[RagState, RagState]):
    def __init__(self, stream_handler: Optional[AsyncStreamingCallbackHandler]):
        self.stream_handler = stream_handler

    def invoke(self, state: RagState) -> RagState:
        raise NotImplementedError("SummarizeDocsNode does not support sync invoke")

    async def ainvoke(
        self,
        state: RagState,
        config: Optional[RunnableConfig] = None,
    ) -> AgentState:
        if not state["docs"]:
            logger.error(f"No documents found for query: {state['user_question']}")
            raise ValueError("No documents found")

        metadatas = SummarizeDocsNode.get_metadatas(state["docs"])
        llm = get_llm_from_config(backend_config, callbacks=[self.stream_handler])
        response = await SummarizeDocsNode.summarize_docs(
            state["user_question"], metadatas, llm
        )

        # TODO: Should Doc ID be used to track metadata on the frontend?
        await self.stream_handler.on_tool_metadata(
            metadata={
                "sources": [doc.id for doc in state["docs"]],
                "image_links": self.get_image_urls(metadatas),
            }
        )
        logger.info(f"Summarized docs: {response.content}")

        return {"messages": [response]}

    @staticmethod
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
            sources="\n".join(SummarizeDocsNode.get_source_urls(metadatas)),
            image_links="\n".join(
                SummarizeDocsNode.get_image_urls(metadatas)
            ),  # TODO: Filter down to a smaller number of images
        )
        logger.info(f"Summarize prompt: {summarize_prompt}")

        return AIMessage.model_validate(await llm.ainvoke(summarize_prompt))

    @staticmethod
    def get_metadatas(docs: list[Document]) -> list[VectorMetadata]:
        return [VectorMetadata.model_validate(doc.metadata) for doc in docs]

    @staticmethod
    def get_source_urls(metadatas: list[VectorMetadata]) -> list[str]:
        return [metadata.url for metadata in metadatas if metadata.url]

    @staticmethod
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
