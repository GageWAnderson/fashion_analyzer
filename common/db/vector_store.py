from pydantic import BaseModel, ConfigDict

from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from common.config.base_config import BaseConfig
from common.utils.llm import get_embedding_model_from_config


class PgVectorStore(BaseModel):
    vector_store: PGVector
    model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_config(cls, config: BaseConfig) -> "PgVectorStore":
        vector_store_from_client = PGVector(
            embeddings=get_embedding_model_from_config(config),
            collection_name=config.vector_store_collection_name,
            connection=cls._get_connection_string_from_config(config),
        )
        return cls(vector_store=vector_store_from_client)

    @staticmethod
    def _get_connection_string_from_config(config: BaseConfig) -> str:
        return f"postgresql+psycopg://{config.postgres_user}:{config.postgres_password}@{config.postgres_host}:{config.postgres_port}/{config.postgres_db}"

    def as_retriever(self) -> VectorStoreRetriever:
        return self.vector_store.as_retriever()
