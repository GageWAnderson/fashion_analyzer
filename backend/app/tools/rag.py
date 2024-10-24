from typing import Type, ClassVar
import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langchain.schema import AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

from backend.app.config.config import backend_config
from common.db.vector_store import PgVectorStore
from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from backend.app.schemas.rag import RagToolInput
from common.utils.llm import get_llm_from_config
from common.schemas.vector_metadata import VectorMetadata


logger = logging.getLogger(__name__)


class RagTool(BaseTool):
    name: ClassVar[str] = "rag_tool"
    description: ClassVar[str] = """Use this tool to answer all user questions."""
    args_schema: Type[BaseModel] = RagToolInput
    stream_handler: AsyncStreamingCallbackHandler = Field(default=None, exclude=True)

    def _run(self, input: str) -> str:
        raise NotImplementedError("RAG tool does not support sync execution.")

    async def _arun(self, input: str) -> str:
        vector_store = PgVectorStore.from_config(backend_config)
        # TODO: Re-enable RAG graph a a sub-graph once streaming performance is improved
        # rag_graph = RagGraph.from_config(
        #     backend_config, vector_store, self.stream_handler
        # )
        retriever = vector_store.as_retriever()
        docs = retriever.invoke(input)
        if not docs:
            logger.error(f"No documents found for query: {input}")
            raise ValueError("No documents found")
        metadatas = RagTool._get_metadatas(docs)
        logger.debug(f"Retrieved {len(docs)} documents")

        # TODO: If the images exist, include their URLs in the response

        prompt = PromptTemplate(
            input_variables=["question", "docs", "sources", "image_links"],
            template=backend_config.summarize_docs_prompt,
        )
        llm = get_llm_from_config(backend_config, callbacks=[self.stream_handler])
        summarize_prompt = prompt.format(
            question=input,
            docs=docs,
            sources="\n".join(RagTool._get_source_urls(metadatas)),
            image_links="\n".join(RagTool._get_image_urls(metadatas)),
        )
        logger.debug(f"Summarize prompt: {summarize_prompt}")

        response = AIMessage.model_validate(await llm.ainvoke(summarize_prompt))

        # TODO: Should Doc ID be used to track metadata on the frontend?
        await self.stream_handler.on_tool_metadata(
            metadata={
                "sources": [doc.id for doc in docs],
                "image_links": RagTool._get_image_urls(metadatas),
            }
        )
        logger.debug(f"Summarized docs: {response.content}")

        return response

    @staticmethod
    def _get_metadatas(docs: list[Document]) -> list[VectorMetadata]:
        return [VectorMetadata.model_validate(doc.metadata) for doc in docs]

    @staticmethod
    def _get_source_urls(metadatas: list[VectorMetadata]) -> list[str]:
        return [metadata.url for metadata in metadatas if metadata.url]

    @staticmethod
    def _get_image_urls(source_metadatas: list[VectorMetadata]) -> list[str]:
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
