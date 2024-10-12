from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult


class DataTypes(Enum):
    ACTION = "action"
    APPENDIX = "appendix"
    LLM = "llm"
    SIGNAL = "signal"
    TEXT = "text"


class Signals(Enum):
    START = "START"
    END = "END"
    TOOL_END = "TOOL_END"
    LLM_END = "LLM_END"
    CHAIN_START = "CHAIN_START"
    CHAIN_END = "CHAIN_END"
    STOP = "STOP"


class StreamingData(BaseModel):
    data: str
    data_type: DataTypes = DataTypes.TEXT
    metadata: dict[str, Any] = Field(default_factory=dict)


class AsyncStreamingCallbackHandler(AsyncCallbackHandler):
    def __init__(self, streaming_function: Callable[[str], None]):
        self.streaming_function = streaming_function
        self.run_id = None

    async def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any
    ) -> None:
        await self.streaming_function(
            StreamingData(
                data=Signals.START.value, data_type=DataTypes.SIGNAL, metadata=kwargs
            ).model_dump_json()
        )

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        await self.streaming_function(
            StreamingData(
                data=token, data_type=DataTypes.LLM, metadata={}
            ).model_dump_json()
        )

    async def on_llm_end(
        self, response: Optional[LLMResult] = None, **kwargs: Any
    ) -> None:
        await self.streaming_function(
            StreamingData(
                data=Signals.END.value, data_type=DataTypes.SIGNAL, metadata=kwargs
            ).model_dump_json()
        )

    async def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        await self.streaming_function(
            StreamingData(
                data=repr(error), data_type=DataTypes.LLM, metadata=kwargs
            ).model_dump_json()
        )

    async def on_tool_start(
        self, serialized: dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        await self.streaming_function(
            StreamingData(
                data=(tool_name := serialized["name"]),
                data_type=DataTypes.ACTION,
                metadata={"tool": tool_name, "step": 0, "time": datetime.now()},
            ).model_dump_json()
        )

    async def on_tool_end(self, output: Optional[Any] = None, **kwargs: Any) -> None:
        await self.streaming_function(
            StreamingData(
                data=Signals.TOOL_END.value,
                data_type=DataTypes.SIGNAL,
                metadata={"tool": kwargs["name"]},
            ).model_dump_json()
        )

    async def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        await self.streaming_function(
            StreamingData(
                data="error",
                data_type=DataTypes.ACTION,
                metadata={"tool": kwargs["name"], "step": 1, "error": repr(error)},
            ).model_dump_json()
        )
