from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AIMessage
from deepeval.models.base_model import DeepEvalBaseLLM

# TODO: Develop a vLLM connector for DeepEval

class DeepEvalLangchainModel(DeepEvalBaseLLM):

    def __init__(self, model: BaseLanguageModel):
        self.model = model

    def load_model(self):
        return self.model

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response for the given prompt.

        Args:
            prompt (str): The input prompt
            n (int, optional): Number of generations (ignored as we return single response). Defaults to 1.
            **kwargs: Additional keyword arguments passed to the model
        """
        return AIMessage.model_validate(self.load_model().invoke(input=prompt)).content

    async def a_generate(self, prompt: str, **kwargs) -> str:
        return AIMessage.model_validate(
            await self.load_model().ainvoke(input=prompt)
        ).content

    def batch_generate(self, prompts: list[str]) -> list[str]:
        return [
            AIMessage.model_validate(res).content
            for res in self.load_model().batch(inputs=prompts)
        ]

    def get_model_name(self):
        return self.model.name

    def set_run_config(self, config: dict) -> None:
        """Set runtime configuration for the model."""
        # If your langchain model needs any runtime configuration,
        # implement the logic here. Otherwise, just pass
        pass
