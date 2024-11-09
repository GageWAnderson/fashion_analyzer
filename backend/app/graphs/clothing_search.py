import re
from typing import Any, Union

from langgraph.graph.state import StateGraph, START, END
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage

from backend.app.config.config import BackendConfig
from backend.app.schemas.subgraph import Subgraph
from backend.app.schemas.clothing import ClothingGraphState
from backend.app.utils.streaming import AsyncStreamingCallbackHandler
from backend.app.nodes.clothing_extractor import ClothingExtractorNode
from backend.app.nodes.clothing_search import ClothingSearchNode
from backend.app.nodes.clothing_parser import ClothingParserNode
from backend.app.config.config import backend_config
from common.utils.llm import get_llm_from_config


class ClothingSearchGraph(Subgraph):
    """
    This graph searches the web for clothing items similar to the one the user is asking about.
    """

    name: str = "clothing_search_graph"
    description: str = (
        """
        Searches the web for clothing items similar to the one the user is asking about.
        Use this tool when your user is asking about a specific clothing item.
        """
    )
    stream_handler: AsyncStreamingCallbackHandler

    @classmethod
    def from_config(
        cls,
        config: BackendConfig,
        stream_handler: AsyncStreamingCallbackHandler,
    ) -> "ClothingSearchGraph":
        llm = get_llm_from_config(config)
        fast_llm = get_llm_from_config(config, config.fast_llm)
        structured_llm = get_llm_from_config(config, config.tool_call_llm)
        graph = StateGraph(ClothingGraphState)
        graph.add_node(
            "clothing_extractor",
            ClothingExtractorNode.from_handler(stream_handler=stream_handler),
        )
        graph.add_node("search", ClothingSearchNode())
        graph.add_node(
            "clothing_parser",
            ClothingParserNode.from_llm_and_handler(
                llm=llm,
                fast_llm=fast_llm,
                structured_llm=structured_llm,
                stream_handler=stream_handler,
            ),
        )

        graph.add_conditional_edges(
            START,
            ClothingSearchGraph.filter_question,
            {True: "clothing_extractor", False: END},
        )
        graph.add_edge("clothing_extractor", "search")
        graph.add_edge("search", "clothing_parser")
        graph.add_edge("clothing_parser", END)
        return cls(
            graph=graph.compile(),
            stream_handler=stream_handler,
        )

    @staticmethod
    async def filter_question(state: ClothingGraphState) -> bool:
        """
        Filters the user question to make sure the user is asking about clothing.
        Terminates the graph if the user is not asking about clothing.
        """
        # TODO: This should be a classifier to save money on LLM calls
        # TODO: Train a BERT classifier to classify questions into clothing or not clothing
        fast_llm = get_llm_from_config(backend_config, llm=backend_config.fast_llm)
        prompt = PromptTemplate(
            input_variables=["user_question"],
            template=backend_config.question_filter_prompt,
        )
        raw_response = AIMessage.model_validate(
            await fast_llm.ainvoke(prompt.format(user_question=state.user_question))
        ).content
        return ClothingSearchGraph.parse_raw_response(raw_response)

    @staticmethod
    async def check_results(state: ClothingGraphState) -> bool:
        """
        Checks the parsed clothing items found to make sure they are
        properly formatted, exist, and have the required metadata to display on the frontend.
        """
        if state.search_retries > backend_config.max_clothing_search_retries:
            return False
        return len(state.parsed_results) > 0

    @staticmethod
    def parse_raw_response(raw_response: str) -> bool:
        return bool(re.search(r"true", raw_response.lower()))
