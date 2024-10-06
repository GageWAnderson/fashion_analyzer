import logging
from typing import Annotated, Type, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from common.utils.llm import get_llm_from_config
from backend.app.config.config import backend_config
from backend.app.utils.streaming import AsyncStreamingCallbackHandler

logger = logging.getLogger(__name__)


class QaToolInput(BaseModel):
    input: Annotated[
        str, "A basic question from the user that you can answer quickly from memory."
    ]


class QaTool(BaseTool):
    name: str = "qa_tool"
    description: str = (
        """This tool answers user questions from your long term memory.
        Use this tool when the question doesn't require data from the past year"""
    )
    args_schema: Type[BaseModel] = QaToolInput
    stream_handler: AsyncStreamingCallbackHandler = Field(default=None, exclude=True)

    def _run(
        self, input: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        raise NotImplementedError("QA tool does not support sync.")

    async def _arun(
        self, input: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        llm = get_llm_from_config(backend_config)
        logger.info(f"qa_tool: {input}")
        return await llm.ainvoke(input, callbacks=[self.stream_handler])
