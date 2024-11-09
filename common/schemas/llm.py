from typing import Literal
from enum import Enum

LLMType = Literal["gpt-4o", "gpt-4o-mini", "llama3.1", "llama3-groq-tool-use"]
EmbeddingModelType = Literal["text-embedding-3-small", "nomic-embed-text"]


class LLMPrefix(Enum):
    OLLAMA = "ollama_"
    VLLM = "vllm_"
    VLLM_TOOL_CALL = "vllm_tool_call_"
