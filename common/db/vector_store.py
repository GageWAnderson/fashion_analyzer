from pydantic import BaseModel

import chromadb
from langchain_chroma import Chroma
from langchain_core.vectorstores.base import VectorStoreRetriever
from common.config.base_config import BaseConfig
from common.utils.llm import get_embedding_model_from_config


class ChromaVectorStore(BaseModel):
    vector_store: Chroma

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_config(cls, config: BaseConfig) -> "ChromaVectorStore":
        persistent_client = chromadb.PersistentClient()
        persistent_client.get_or_create_collection(config.vector_store_collection_name)
        vector_store_from_client = Chroma(
            client=persistent_client,
            collection_name=config.vector_store_collection_name,
            embedding_function=get_embedding_model_from_config(config),
        )
        return cls(vector_store=vector_store_from_client)

    def as_retriever(self) -> VectorStoreRetriever:
        return self.vector_store.as_retriever()
