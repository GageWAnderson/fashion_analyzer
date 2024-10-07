from langchain_core.runnables import Runnable
from langchain_core.language_models import BaseLanguageModel

from backend.app.schemas.rag import RagGraphState
from backend.app.utils.streaming import AsyncStreamingCallbackHandler


class SummarizeDocsNode(Runnable[RagGraphState, RagGraphState]):
    def __init__(
        self, llm: BaseLanguageModel, stream_handler: AsyncStreamingCallbackHandler
    ):
        self.llm = llm
        self.stream_handler = stream_handler

    def invoke(self, state: RagGraphState) -> RagGraphState:
        raise NotImplementedError("SummarizeDocsNode does not support sync invoke")

    async def ainvoke(self, state: RagGraphState) -> RagGraphState:
        return {
            "generation": await self.llm.astream(
                state["docs"], callbacks=[self.stream_handler]
            )
        }
