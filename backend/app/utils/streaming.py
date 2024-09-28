from datetime import datetime
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel

from langchain_core.callbacks import AsyncCallbackHandler


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
    metadata: dict[str, Any] = {}


class AsyncStreamingCallbackHandler(AsyncCallbackHandler):
    def __init__(
        self, streaming_function: Callable[[str, DataTypes, dict[str, Any]], None]
    ):
        self.streaming_function = streaming_function
        self.run_id = None

    async def on_llm_start(self, **kwargs: Any) -> None:
        await self.streaming_function(
            data=Signals.START.value, data_type=DataTypes.SIGNAL, metadata=kwargs
        )

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        await self.streaming_function(data=token, data_type=DataTypes.LLM, metadata={})

    async def on_llm_end(self, **kwargs: Any) -> None:
        await self.streaming_function(
            data=Signals.END.value, data_type=DataTypes.SIGNAL, metadata=kwargs
        )

    async def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        await self.streaming_function(
            data=repr(error), data_type=DataTypes.LLM, metadata=kwargs
        )

    async def on_tool_start(self, serialized: dict[str, Any], **kwargs: Any) -> None:
        await self.streaming_function(
            data=(tool_name := serialized["name"]),
            data_type=DataTypes.ACTION,
            metadata=kwargs | {"tool": tool_name, "step": 0, "time": datetime.now()},
        )

    async def on_tool_end(self, **kwargs: Any) -> None:
        await self.streaming_function(
            data=Signals.TOOL_END.value,
            data_type=DataTypes.SIGNAL,
            metadata=kwargs | {"tool": kwargs["name"]},
        )

    async def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        await self.streaming_function(
            data=repr(error),
            data_type=DataTypes.ACTION,
            metadata=kwargs | {"tool": kwargs["name"]},
        )
