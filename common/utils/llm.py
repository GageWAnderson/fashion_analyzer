from typing import Optional
from functools import partial
import httpx

from langchain_openai import ChatOpenAI
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.language_models import BaseLanguageModel
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.callbacks import AsyncCallbackHandler

from backend.app.config.config import backend_config
from common.config.base_config import BaseConfig
from common.schemas.llm import LLMPrefix
from common.utils.vllm import VLLMClient


def get_llm_from_config(
    config: BaseConfig,
    llm: Optional[str] = None,
    callbacks: Optional[list[AsyncCallbackHandler]] = None,
) -> BaseLanguageModel:
    """
    Get a LLM from the config. If a LLM is not specified, the default LLM is used.
    Since ChatOllama doesn't have async parallel calling support, we give the option
    of connecting to a remote vLLM server instead for parallel calling.
    """
    if llm is None:
        llm = config.llm

    http_async_client = httpx.AsyncClient()
    chat_ollama = partial(
        ChatOllama,
        base_url=config.ollama_url,
        verbose=True,
        temperature=config.llm_temperature,
        callbacks=callbacks,
        http_async_client=http_async_client,
    )

    match llm:
        case "gpt-4o":
            return ChatOpenAI(
                model="gpt-4o",
                api_key=config.openai_api_key,
                temperature=config.llm_temperature,
                callbacks=callbacks,
                streaming=True,
                verbose=True,
                http_async_client=http_async_client,
            )
        case "gpt-4o-mini":
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=config.openai_api_key,
                temperature=config.llm_temperature,
                callbacks=callbacks,
                streaming=True,
                verbose=True,
                cache=False,  # Cache is disabled to always render responses
                http_async_client=http_async_client,
            )
        case str() if LLMPrefix.OLLAMA.value in llm:
            model_name = llm.split("_")[1]
            return chat_ollama(model=model_name)
        case str() if LLMPrefix.VLLM.value in llm:
            model_name = llm.split("_")[1]
            return VLLMClient(
                openai_api_key="EMPTY",
                openai_api_base=backend_config.vllm_url,
                model_name=model_name,
                streaming=True,
                callbacks=callbacks,
            )
        case _:
            raise ValueError(f"Invalid LLM: {llm}")


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
