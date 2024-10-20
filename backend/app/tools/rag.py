from typing import Type, ClassVar
import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.language_models import BaseLanguageModel
from langchain.schema import AIMessage
from langchain_core.prompts import PromptTemplate

from backend.app.graphs.rag import RagGraph
from backend.app.config.config import backend_config
from common.db.vector_store import ChromaVectorStore
from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from backend.app.schemas.rag import RagToolInput
from common.utils.llm import get_llm_from_config

# from backend.app.nodes.retrieve import RetrieveNode
# from backend.app.nodes.grade_docs import GradeDocsNode
# from backend.app.nodes.summarize_docs import SummarizeDocsNode


logger = logging.getLogger(__name__)


class RagTool(BaseTool):
    name: ClassVar[str] = "rag_tool"
    description: ClassVar[str] = """Use this tool to answer all user questions."""
    args_schema: Type[BaseModel] = RagToolInput
    stream_handler: AsyncStreamingCallbackHandler = Field(default=None, exclude=True)

    def _run(self, input: str) -> str:
        raise NotImplementedError("RAG tool does not support sync execution.")

    async def _arun(self, input: str) -> str:
        vector_store = ChromaVectorStore.from_config(backend_config)
        # TODO: Re-enable RAG graph once streaming performance is improved
        # rag_graph = RagGraph.from_config(
        #     backend_config, vector_store, self.stream_handler
        # )
        retriever = vector_store.as_retriever()
        docs = await retriever.ainvoke(input)
        logger.info(f"Retrieved {len(docs)} documents")
        prompt = PromptTemplate(
            input_variables=["question", "docs"],
            template=backend_config.summarize_docs_prompt,
        )
        llm = get_llm_from_config(backend_config, callbacks=[self.stream_handler])
        response = AIMessage.model_validate(
            await llm.ainvoke(
                prompt.format(question=input, docs=docs),
            )
        )
        logger.info(f"Summarized docs: {response.content}")
        return response.content
