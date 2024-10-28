import logging
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict
from langchain_core.prompts import PromptTemplate
from langchain.schema import AIMessage
from langchain_core.language_models import BaseLanguageModel

from backend.app.schemas.summary import WeeklySummaryResponse
from backend.app.config.config import BackendConfig, backend_config
from backend.app.exceptions.sources import NotEnoughSourcesException
from backend.app.nodes.summarize_docs import SummarizeDocsNode
from common.utils.llm import get_llm_from_config
from common.db.vector_store import PgVectorStore

logger = logging.getLogger(__name__)


class SummaryService(BaseModel):
    """Service for generating summaries."""

    llm: BaseLanguageModel
    vector_store: PgVectorStore
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    async def from_config(cls, config: BackendConfig) -> "SummaryService":
        vector_store = await PgVectorStore.from_config(config)
        return cls(llm=get_llm_from_config(config), vector_store=vector_store)

    async def generate_summary(self, weeks: int, days: int) -> WeeklySummaryResponse:
        retriever = self.vector_store.as_retriever(
            # filter=self._get_age_filter(weeks, days) TODO: Re-enable metadata filtering
        )
        docs = retriever.invoke(backend_config.summarize_weekly_prompt)

        if not docs:
            raise NotEnoughSourcesException(
                f"Not enough documents found, found {len(docs)} documents"
            )

        metadatas = SummarizeDocsNode.get_metadatas(docs)
        image_urls = SummarizeDocsNode.get_image_urls(metadatas)
        sources = SummarizeDocsNode.get_source_urls(metadatas)

        if not self._has_enough_sources_for_summary(sources):
            raise NotEnoughSourcesException("Not enough sources found")

        summary = (
            await SummarizeDocsNode.summarize_docs(
                backend_config.summarize_weekly_prompt, metadatas, self.llm
            )
        ).content
        return WeeklySummaryResponse(
            text=str(summary), sources=sources, images=image_urls
        )

    # @staticmethod
    # def _get_age_filter(weeks: int, days: int) -> dict:
    #     one_week_ago = datetime.now() - timedelta(weeks=weeks, days=days)
    #     # TODO: Think of the correct way to use metadata filtering with PGVector
    #     return {
    #         "query": """
    #             SELECT * FROM langchain_pg_embedding
    #             WHERE cmetadata->>'timestamp' < %s
    #             AND cmetadata->>'timestamp' > %s
    #         """,
    #         "params": (
    #             datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
    #             one_week_ago.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    #         ),
    #     }

    @staticmethod
    def _has_enough_sources_for_summary(sources: list[str]) -> bool:
        return len(sources) > backend_config.min_sources_for_summary
