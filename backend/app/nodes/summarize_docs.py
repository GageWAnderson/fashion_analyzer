from typing import Optional
import logging
from langchain_core.runnables import Runnable, RunnableConfig

from backend.app.schemas.rag import RagState
from backend.app.schemas.agent_state import AgentState
from backend.app.config.config import backend_config
from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from common.utils.llm import get_llm_from_config
from backend.app.utils.rag import summarize_docs, get_metadatas, get_image_urls

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

        metadatas = get_metadatas(state["docs"])
        llm = get_llm_from_config(
            backend_config,
            llm=backend_config.summarize_llm,
            callbacks=[self.stream_handler],
        )
        response = await summarize_docs(state["user_question"], metadatas, llm)

        # TODO: Should Doc ID be used to track metadata on the frontend?
        await self.stream_handler.on_tool_metadata(
            metadata={
                "sources": [doc.id for doc in state["docs"]],
                "image_links": get_image_urls(metadatas),
            }
        )
        logger.info(f"Summarized docs: {response.content}")

        return {"messages": [response]}
