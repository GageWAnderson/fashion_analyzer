from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.language_models import BaseLanguageModel
from langchain_ollama import ChatOllama, OllamaEmbeddings

from common.schemas.llm import LLMType, EmbeddingModelType
from common.config.base_config import base_config


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
            return ChatOllama(
                base_url=base_config.ollama_url,
                model="llama3.1",
                temperature=temperature,
            )
        case "llama3-groq-tool-use":
            return ChatOllama(
                model="llama3-groq-tool-use:latest", temperature=temperature
            )
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
            return OllamaEmbeddings(
                base_url=base_config.ollama_url,
                model="nomic-embed-text",
                temperature=temperature,
            )
        case _:
            raise ValueError(f"Invalid embedding model: {embedding_model}")
