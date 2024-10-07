from langchain_core.runnables import Runnable

from backend.app.schemas.rag import RagGraphState
from common.db.vector_store import ChromaVectorStore


class RetrieveNode(Runnable[RagGraphState, RagGraphState]):
    def __init__(self, vector_store: ChromaVectorStore):
        self.retriever = vector_store.as_retriever()

    def invoke(self, state: RagGraphState) -> RagGraphState:
        raise NotImplementedError("RetrieveNode does not support sync invoke")

    async def ainvoke(self, state: RagGraphState) -> RagGraphState:
        return await self.retriever.aget_relevant_documents(state["question"])
