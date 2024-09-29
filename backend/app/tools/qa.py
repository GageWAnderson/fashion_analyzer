from typing import Annotated

from langchain_core.tools import tool
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import StructuredTool

from app.services.llm import get_llm
from app.core.config import settings


@tool
async def qa_tool(
    input: Annotated[
        str, "A basic question from the user that you can answer quickly from memory."
    ],
) -> StructuredTool:
    """This tool answers user questions from your long term memory.
    Use this tool when the question doesn't require data from the past year"""
    llm = get_llm(settings.OLLAMA_BASE_MODEL)
    return await llm.ainvoke(input)
