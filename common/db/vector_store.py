from pydantic import BaseModel, ConfigDict

from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from common.config.base_config import BaseConfig
from common.utils.llm import get_embedding_model_from_config


class PgVectorStore(BaseModel):
    vector_store: PGVector
    vector_search_type: str
    vector_search_k: int
    vector_search_fetch_k: int
    model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    async def from_config(cls, config: BaseConfig) -> "PgVectorStore":
        vector_store_from_client = PGVector(
            embeddings=get_embedding_model_from_config(config),
            collection_name=config.vector_store_collection_name,
            connection=cls._get_connection_string_from_config(config),
        )
        return cls(
            vector_store=vector_store_from_client,
            vector_search_type=config.vector_search_type,
            vector_search_k=config.vector_search_k,
            vector_search_fetch_k=config.vector_search_fetch_k,
        )

    @staticmethod
    def _get_connection_string_from_config(config: BaseConfig) -> str:
        return f"postgresql://{config.postgres_user}:{config.postgres_password}@{config.postgres_host}:{config.postgres_port}/{config.postgres_db}"

    def as_retriever(self, filter: dict = {}) -> VectorStoreRetriever:
        return self.vector_store.as_retriever(
            search_type=self.vector_search_type,
            search_kwargs={
                "k": self.vector_search_k,
                "fetch_k": self.vector_search_fetch_k,
                "filter": filter,
            },
        )
