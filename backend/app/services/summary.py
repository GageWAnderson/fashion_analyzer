import logging
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict
from langchain_core.prompts import PromptTemplate
from langchain.schema import AIMessage
from langchain_core.language_models import BaseLanguageModel

from backend.app.schemas.summary import WeeklySummaryResponse
from backend.app.tools.rag import RagTool
from backend.app.config.config import BackendConfig, backend_config
from backend.app.exceptions.sources import NotEnoughSourcesException
from common.utils.llm import get_llm_from_config
from common.db.vector_store import PgVectorStore

logger = logging.getLogger(__name__)


class SummaryService(BaseModel):
    """Service for generating summaries."""

    llm: BaseLanguageModel
    vector_store: PgVectorStore
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_config(cls, config: BackendConfig) -> "SummaryService":
        vector_store = PgVectorStore.from_config(config)
        return cls(llm=get_llm_from_config(config), vector_store=vector_store)

    async def generate_summary(self, weeks: int, days: int) -> WeeklySummaryResponse:
        retriever = self.vector_store.as_retriever(
            filter=self._get_age_filter(weeks, days)
        )
        docs = await retriever.ainvoke(backend_config.summarize_weekly_prompt)

        if not docs:
            raise NotEnoughSourcesException(
                f"Not enough documents found, found {len(docs)} documents"
            )

        metadatas = RagTool.get_metadatas(docs)
        image_urls = RagTool.get_image_urls(metadatas)
        sources = RagTool.get_source_urls(metadatas)
        if not SummaryService._has_enough_sources_for_summary(sources):
            raise NotEnoughSourcesException("Not enough sources found")
        prompt = PromptTemplate(
            input_variables=["question", "docs", "sources", "image_links"],
            template=backend_config.summarize_docs_prompt,
        )
        summarize_prompt = prompt.format(
            question=backend_config.summarize_weekly_prompt,
            docs=docs,
            sources="\n".join(sources),
            image_links="\n".join(image_urls),
        )
        summary = AIMessage.model_validate(
            await self.llm.ainvoke(summarize_prompt)
        ).content
        return WeeklySummaryResponse(
            text=str(summary), sources=sources, images=image_urls
        )

    @staticmethod
    def _get_age_filter(weeks: int, days: int) -> dict:
        return {
            "timestamp": {"$gte": datetime.now() - timedelta(weeks=weeks, days=days)}
        }

    @staticmethod
    def _has_enough_sources_for_summary(sources: list[str]) -> bool:
        return len(sources) > backend_config.min_sources_for_summary
