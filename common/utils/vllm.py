from typing import Any, Optional

from langchain_core.runnables import RunnableConfig, ensure_config
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage
from langchain_community.llms.vllm import VLLMOpenAI


class VLLMClient(VLLMOpenAI):
    """
    A wrapper around the VLLMOpenAI that supports the langchain interface.
    """

    async def ainvoke(
        self,
        input: LanguageModelInput,
        config: Optional[RunnableConfig] = None,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> str:
        config = ensure_config(config)
        llm_result = await self.agenerate_prompt(
            [self._convert_input(input)],
            stop=stop,
            callbacks=config.get("callbacks"),
            tags=config.get("tags"),
            metadata=config.get("metadata"),
            run_name=config.get("run_name"),
            run_id=config.pop("run_id", None),
        )
        raw_res = llm_result.generations[0][0].text
        return AIMessage(content=raw_res)
