from typing import Optional
import logging

from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.prompts import PromptTemplate

from backend.app.schemas.clothing import ClothingGraphState
from backend.app.schemas.clothing import ClothingItem
from backend.app.config.config import backend_config
from common.utils.llm import get_llm_from_config

logger = logging.getLogger(__name__)


class ClothingParserNode(Runnable[ClothingGraphState, ClothingGraphState]):

    def invoke(self, state: ClothingGraphState) -> ClothingGraphState:
        raise NotImplementedError("ClothingParserNode does not support sync invoke")

    async def ainvoke(
        self, state: ClothingGraphState, config: Optional[RunnableConfig] = None
    ) -> ClothingGraphState:
        raw_search_results = state.search_results
        res = []
        for raw_res in raw_search_results:
            try:
                parsed_clothing_item = await self.parse_raw_res(raw_res)
                res.append(
                    ClothingItem(
                        **parsed_clothing_item.model_dump(), image_url=raw_res["url"]
                    )
                )
            except Exception:
                logger.warning(f"Failed to parse clothing item from {raw_res['url']}")
                continue
        return {"parsed_results": res}

    async def parse_raw_res(self, raw_res: dict) -> ClothingItem:
        llm = get_llm_from_config(backend_config).with_structured_output(ClothingItem)

        # TODO: Figure out how to extract multiple clothing items per page
        # Will require a clever prompting/chunking strategy
        prompt = PromptTemplate(
            input_variables=["content"],
            template=backend_config.clothing_search_result_parser_prompt,
        )
        extract_prompt = prompt.format(content=raw_res["content"])
        logger.info(f"Extract prompt: {extract_prompt}")
        return ClothingItem.model_validate(await llm.ainvoke(extract_prompt))
