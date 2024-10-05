
from langchain_openai import ChatOpenAI
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.language_models import BaseLanguageModel
from langchain_ollama import ChatOllama, OllamaEmbeddings

from common.config.base_config import BaseConfig


def get_llm_from_config(
    config: BaseConfig,
) -> BaseLanguageModel:
    match config.llm:
        case "gpt-4o":
            return ChatOpenAI(
                model="gpt-4o",
                api_key=config.openai_api_key,
                temperature=config.llm_temperature,
            )
        case "gpt-4o-mini":
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=config.openai_api_key,
                temperature=config.llm_temperature,
            )
        case "llama3.1":
            return ChatOllama(
                base_url=config.ollama_url,
                model="llama3.1",
                temperature=config.llm_temperature,
            )
        case "llama3-groq-tool-use":
            return ChatOllama(
                model="llama3-groq-tool-use:latest", temperature=config.llm_temperature
            )
        # TODO: Add more Ollama models
        # TODO: Add vLLM models
        case _:
            raise ValueError(f"Invalid LLM: {config.llm}")


def get_embedding_model_from_config(
    config: BaseConfig,
) -> Embeddings:
    match config.embedding_model:
        case "text-embedding-3-small":
            return OpenAIEmbeddings(
                model="text-embedding-3-small", api_key=config.openai_api_key
            )
        case "nomic-embed-text":
            return OllamaEmbeddings(
                base_url=config.ollama_url,
                model="nomic-embed-text",
            )
        case _:
            raise ValueError(f"Invalid embedding model: {config.embedding_model}")
