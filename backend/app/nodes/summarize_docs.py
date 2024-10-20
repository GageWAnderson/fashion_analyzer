from typing import Optional
import logging
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.language_models import BaseLanguageModel
from langchain.schema import AIMessage
from langchain_core.prompts import PromptTemplate

from backend.app.schemas.rag import RagGraphState
from backend.app.config.config import backend_config
from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from common.utils.llm import get_llm_from_config

logger = logging.getLogger(__name__)


class SummarizeDocsNode(Runnable[RagGraphState, RagGraphState]):
    def __init__(self, stream_handler: AsyncStreamingCallbackHandler):
        self.stream_handler = stream_handler

    def invoke(self, state: RagGraphState) -> RagGraphState:
        raise NotImplementedError("SummarizeDocsNode does not support sync invoke")

    async def ainvoke(
        self,
        state: RagGraphState,
        config: Optional[RunnableConfig] = None,
    ) -> RagGraphState:
        prompt = PromptTemplate(
            input_variables=["question", "docs"],
            template=backend_config.summarize_docs_prompt,
        )
        llm = get_llm_from_config(backend_config, callbacks=[self.stream_handler])
        response = AIMessage.model_validate(
            await llm.ainvoke(
                prompt.format(question=state["question"], docs=state["docs"]),
            )
        )
        logger.info(f"Summarized docs: {response.content}")

        return {"answer": response.content}
