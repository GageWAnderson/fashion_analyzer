from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseLanguageModel
from langchain_ollama import ChatOllama

from app.schemas.llm import LLMType


def get_llm(
    llm: LLMType, api_key: Optional[str] = None, temperature: float = 0.0
) -> BaseLanguageModel:
    match llm:
        case "gpt-4o":
            return ChatOpenAI(model="gpt-4o", api_key=api_key, temperature=temperature)
        case "llama3.1":
            return ChatOllama(model="llama3.1", temperature=temperature)
        # TODO: Add more Ollama models
        # TODO: Add vLLM models
        case _:
            raise ValueError(f"Invalid LLM: {llm}")
