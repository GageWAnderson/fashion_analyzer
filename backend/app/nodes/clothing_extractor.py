from typing import Optional
import asyncio
import logging

from pydantic import BaseModel, ConfigDict
from langchain_core.runnables import Runnable, RunnableConfig
from langchain.schema import AIMessage
from langchain_core.prompts import PromptTemplate

from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from backend.app.schemas.clothing import (
    ClothingGraphState,
    ClothingSearchQuery,
    ClothingItem,
)
from backend.app.config.config import backend_config
from common.utils.llm import get_llm_from_config

logger = logging.getLogger(__name__)


class ClothingExtractorNode(
    BaseModel, Runnable[ClothingGraphState, ClothingGraphState]
):
    name: str = "clothing_extractor_node"
    stream_handler: AsyncStreamingCallbackHandler
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_handler(
        cls, stream_handler: AsyncStreamingCallbackHandler
    ) -> "ClothingExtractorNode":
        return cls(stream_handler=stream_handler)

    def invoke(self, state: ClothingGraphState) -> ClothingGraphState:
        raise NotImplementedError("ClothingExtractorNode does not support sync invoke")

    async def ainvoke(
        self, state: ClothingGraphState, config: Optional[RunnableConfig] = None
    ) -> ClothingGraphState:
        # llm = get_llm_from_config(backend_config, llm=backend_config.fast_llm)
        # prompt = PromptTemplate(
        #     input_variables=["user_question"],
        #     template=backend_config.clothing_extractor_prompt,
        # )
        # raw_response = AIMessage.model_validate(
        #     await llm.ainvoke(prompt.format(user_question=state.user_question))
        # )
        # logger.info(f"Raw extracted query response: {raw_response}")
        # return {
        #     "search_item": ClothingSearchQuery(query=str(raw_response.content)),
        # }
        # TODO: Re-enable LLM extraction for openAI models
        # NOTE: Different prompts are required for different LLMs, causes more complexity
        # In the codebase - making clean code for this is key for AI engineering
        return {
            "search_item": ClothingSearchQuery(query=state.user_question),
        }
