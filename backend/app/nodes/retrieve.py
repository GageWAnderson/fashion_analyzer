from typing import Optional
import logging

from langchain_core.runnables import Runnable, RunnableConfig

from backend.app.schemas.rag import RagState
from common.db.vector_store import PgVectorStore

logger = logging.getLogger(__name__)


class RetrieveNode(Runnable[RagState, RagState]):
    def __init__(self, vector_store: PgVectorStore):
        self.retriever = vector_store.as_retriever()

    def invoke(self, state: RagState) -> RagState:
        raise NotImplementedError("RetrieveNode does not support sync invoke")

    async def ainvoke(
        self,
        state: RagState,
        config: Optional[RunnableConfig] = None,
    ) -> RagState:
        docs = self.retriever.invoke(state["user_question"])
        logger.info(f"Retrieved {len(docs)} documents")
        # TODO: Augment with BM25 retrieval using Rank-BM25
        # https://github.com/dorianbrown/rank_bm25
        return {
            "user_question": state["user_question"],
            "messages": state["messages"],
            "docs": docs,
        }
