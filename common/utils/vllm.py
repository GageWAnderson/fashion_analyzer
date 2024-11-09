from typing import Any, Optional
import logging
import json

from langchain_core.runnables import RunnableConfig, ensure_config
from langchain_core.language_models import LanguageModelInput
from langchain_community.llms.vllm import VLLMOpenAI
from langchain_core.messages import AIMessage
from langchain_core.utils.function_calling import convert_to_openai_function
from openai import AsyncOpenAI
from langchain_core.tools import Tool


logger = logging.getLogger(__name__)


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


# TODO: Merge these 2 classes to allow VLLMOpenAI to call tools if needed
class VLLMToolCallClient(AsyncOpenAI):
    """
    A wrapper around the OpenAI client that supports the langchain interface.
    """

    async def ainvoke_with_tools(
        self,
        query: LanguageModelInput,
        tools: list[dict],
        config: Optional[RunnableConfig] = None,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Asynchronously invoke the OpenAI client with tools.
        Returns the structured output as tool calls.
        """
        models = await self.models.list()
        model = models.data[0].id
        # tools = [convert_to_openai_function(tool) for tool in tools]
        chat_completion = await self.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": query}],
            tools=tools,
        )
        try:
            function_args = (
                chat_completion.choices[0].message.tool_calls[0].function.arguments
            )
            if isinstance(function_args, str):
                return json.loads(function_args)
            elif isinstance(function_args, dict):
                return function_args
            else:
                raise ValueError(
                    f"Unexpected tool call arguments type: {type(function_args)}"
                )
        except IndexError as e:
            logger.warning("Error extracting tool calls")
            raise ValueError("No tool calls found in response") from e
