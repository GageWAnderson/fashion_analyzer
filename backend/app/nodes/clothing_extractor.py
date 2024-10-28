from typing import Optional
import logging

from langchain_core.runnables import Runnable, RunnableConfig
from langchain.schema import AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel

from backend.app.schemas.clothing import ClothingGraphState, ClothingSearchQuery
from backend.app.config.config import backend_config
from common.utils.llm import get_llm_from_config

logger = logging.getLogger(__name__)


class ClothingExtractorNode(Runnable[ClothingGraphState, ClothingGraphState]):

    def invoke(self, state: ClothingGraphState) -> ClothingGraphState:
        raise NotImplementedError("ClothingExtractorNode does not support sync invoke")

    async def ainvoke(
        self, state: ClothingGraphState, config: Optional[RunnableConfig] = None
    ) -> ClothingGraphState:
        # TODO: Consider disabling structured output for some LLMs
        llm = get_llm_from_config(backend_config).with_structured_output(
            ClothingSearchQuery
        )
        prompt = PromptTemplate(
            input_variables=["user_question"],
            template=backend_config.clothing_extractor_prompt,
        )
        raw_response = await llm.ainvoke(
            prompt.format(user_question=state["user_question"])
        )
        parsed_response = ClothingSearchQuery.model_validate(raw_response)
        return {
            "search_item": parsed_response.query,
        }
