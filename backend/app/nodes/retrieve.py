from typing import Optional
import logging

from langchain_core.runnables import Runnable, RunnableConfig

from backend.app.schemas.rag import RagGraphState
from common.db.vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class RetrieveNode(Runnable[RagGraphState, RagGraphState]):
    def __init__(self, vector_store: ChromaVectorStore):
        self.retriever = vector_store.as_retriever()

    def invoke(self, state: RagGraphState) -> RagGraphState:
        raise NotImplementedError("RetrieveNode does not support sync invoke")

    async def ainvoke(
        self,
        state: RagGraphState,
        config: Optional[RunnableConfig] = None,
    ) -> RagGraphState:
        docs = await self.retriever.ainvoke(state["question"])
        logger.info(f"Retrieved {len(docs)} documents")
        return {"docs": docs}
