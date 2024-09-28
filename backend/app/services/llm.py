from typing import Optional

from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool
from langchain_core.language_models import BaseLanguageModel

from app.schemas.llm import LLMType


def get_llm(llm: LLMType, api_key: Optional[str] = None) -> BaseLanguageModel:
    match llm:
        case "gpt-4o":
            return ChatOpenAI(model="gpt-4o")
        # TODO: Add Ollama models
        # TODO: Add vLLM models
        case _:
            raise ValueError(f"Invalid LLM: {llm}")


def get_tools() -> list[StructuredTool]:
    return []
