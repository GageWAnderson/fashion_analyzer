from pydantic import BaseModel

import chromadb
from langchain_community.vectorstores import VectorStore
from langchain_chroma import Chroma

from crawler.schemas.config import CrawlerConfig


class ChromaVectorStore(BaseModel):
    vector_store: VectorStore

    @classmethod
    def from_config(cls, config: CrawlerConfig) -> "ChromaVectorStore":
        persistent_client = chromadb.PersistentClient()
        persistent_client.get_or_create_collection(config.vector_store_collection_name)
        vector_store_from_client = Chroma(
            client=persistent_client,
            collection_name=config.vector_store_collection_name,
            embedding_function=config.embedding_model,
        )
        return cls(vector_store=vector_store_from_client)
