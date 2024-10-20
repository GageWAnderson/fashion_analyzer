import logging
from typing import Annotated, Type, Optional, ClassVar

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.messages import AIMessage
from common.utils.llm import get_llm_from_config
from backend.app.config.config import backend_config
from backend.app.utils.streaming import AsyncStreamingCallbackHandler

logger = logging.getLogger(__name__)


class QaToolInput(BaseModel):
    input: Annotated[
        str, "A basic question from the user that you can answer quickly from memory."
    ]


class QaTool(BaseTool):
    name: ClassVar[str] = "qa_tool"
    description: ClassVar[str] = """Use this tool to answer all user questions."""
    args_schema: Type[BaseModel] = QaToolInput
    stream_handler: AsyncStreamingCallbackHandler = Field(default=None, exclude=True)

    def _run(
        self, input: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        raise NotImplementedError("QA tool does not support sync.")

    async def _arun(
        self, input: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        llm = get_llm_from_config(backend_config, callbacks=[self.stream_handler])
        response = await llm.ainvoke(input)
        ai_message = AIMessage(content=response.content)
        logger.debug(f"QA tool response: {ai_message}")
        return ai_message.content
