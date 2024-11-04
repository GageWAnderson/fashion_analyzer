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
        llm = get_llm_from_config(backend_config)
        prompt = PromptTemplate(
            input_variables=["user_question"],
            template=backend_config.clothing_extractor_prompt,
        )
        raw_response = AIMessage.model_validate(
            await llm.ainvoke(prompt.format(user_question=state.user_question))
        )
        for i in range(2):
            await self.stream_handler.on_extracted_item(
                item=ClothingItem(
                    name=f"Test Item {i}",
                    price=19.99,
                    link="https://www.pexels.com/search/shoes/",
                    image_url="https://images.pexels.com/photos/5214139/pexels-photo-5214139.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=500",
                )
            )
            await asyncio.sleep(1)
        return {
            "search_item": ClothingSearchQuery(query=str(raw_response.content)),
        }
