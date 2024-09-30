from pydantic import BaseModel

import chromadb
from langchain_community.vectorstores import VectorStore
from langchain_chroma import Chroma

from app.core.config import settings

# Vector store connection object


class ChromaVectorStore(BaseModel):
    vector_store: VectorStore

    @classmethod
    def from_config(cls) -> "ChromaVectorStore":
        persistent_client = chromadb.PersistentClient()
        persistent_client.get_or_create_collection(settings.VECTOR_STORE_COLLECTION_NAME)
        vector_store_from_client = Chroma(
            client=persistent_client,
            collection_name=settings.VECTOR_STORE_COLLECTION_NAME,
            embedding_function=settings.VECTOR_STORE_EMBEDDING_FUNCTION,
        )
        return cls(vector_store=vector_store_from_client)
