from typing import Optional, Literal

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseLanguageModel
from langchain_ollama import ChatOllama
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.embeddings import Embeddings


LLMType = Literal["gpt-4o", "gpt-4o-mini", "llama3.1"]
EmbeddingModelType = Literal["text-embedding-3-small", "nomic-embed-text"]


def get_llm(
    llm: LLMType, api_key: Optional[str] = None, temperature: float = 0.0
) -> BaseLanguageModel:
    match llm:
        case "gpt-4o":
            return ChatOpenAI(model="gpt-4o", api_key=api_key, temperature=temperature)
        case "gpt-4o-mini":
            return ChatOpenAI(
                model="gpt-4o-mini", api_key=api_key, temperature=temperature
            )
        case "llama3.1":
            return ChatOllama(model="llama3.1", temperature=temperature)
        # TODO: Add more Ollama models
        # TODO: Add vLLM models
        case _:
            raise ValueError(f"Invalid LLM: {llm}")


def get_embedding_model(
    embedding_model: EmbeddingModelType,
    api_key: Optional[str] = None,
    temperature: float = 0.0,
) -> Embeddings:
    match embedding_model:
        case "text-embedding-3-small":
            return OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
        case "nomic-embed-text":
            return OllamaEmbeddings(model="nomic-embed-text", temperature=temperature)
        case _:
            raise ValueError(f"Invalid embedding model: {embedding_model}")
