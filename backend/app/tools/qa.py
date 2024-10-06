import logging
from typing import Annotated

from langchain_core.tools import tool
from langchain_core.tools import StructuredTool

from common.utils.llm import get_llm_from_config
from backend.app.config.config import backend_config
from backend.app.utils.streaming import AsyncStreamingCallbackHandler

logger = logging.getLogger(__name__)


@tool # TODO: Change this to a class rather than a function
async def qa_tool(
    stream_handler: AsyncStreamingCallbackHandler,
    input: Annotated[
        str, "A basic question from the user that you can answer quickly from memory."
    ],
) -> StructuredTool:
    """This tool answers user questions from your long term memory.
    Use this tool when the question doesn't require data from the past year"""
    llm = get_llm_from_config(backend_config)
    logger.info(f"qa_tool: {input}")
    return await llm.ainvoke(input, callbacks=[stream_handler])
