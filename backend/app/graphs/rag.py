from functools import partial
from typing import Annotated, Literal, TypedDict, Optional, Union
import operator

from pydantic import BaseModel

from langchain.tools import StructuredTool
from langchain.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langchain_community.vectorstores import VectorStore
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from backend.app.config.config import BackendConfig
from backend.app.utils.streaming import AsyncStreamingCallbackHandler


class RagGraphState(TypedDict):
    question: Annotated[str, operator.add]
    docs: Annotated[list[Document], operator.add]
    answer: Annotated[str, operator.add]
    search: Annotated[str, operator.add]


class DocumentGrade(BaseModel):
    grade: Literal["yes", "no"]
    reason: Optional[str]


async def retrieve(
    retriever: BaseRetriever, query: str
) -> dict[Literal["documents"], list[Document]]:
    return {"documents": await retriever.aget_relevant_documents(query)}


async def grade_docs(
    llm: BaseLanguageModel, state: RagGraphState
) -> dict[Literal["documents", "search"], Union[list[Document], bool]]:
    grade_docs_prompt = PromptTemplate.from_template(
        """
        You are a helpful assistant that grades the relevance of documents to a user's question.
        You are given a document and a user's question. You must determine if the document is relevant to the question.
        You must return a grade of "yes" if the document is relevant, and "no" if the document is not relevant.
        You must return a reason for your grade.
        """
    )

    async def grade_doc(doc: Document) -> bool:
        grading_chain = grade_docs_prompt | llm.with_structured_output(DocumentGrade)
        return (
            "yes"
            == (  # TODO: Might need less stringent requirements for weaker LLMs
                await grading_chain.ainvoke(
                    {"question": state["question"], "doc": doc.page_content}
                ).grade
            )
        )

    return {
        "documents": (filtered_docs := [*(filter(grade_doc, state["docs"]))]),
        "search": len(filtered_docs) == len(state["docs"]),
    }


async def generate(
    llm: BaseLanguageModel,
    state: RagGraphState,
    config: RunnableConfig,
    stream_handler: AsyncStreamingCallbackHandler,
) -> dict[Literal["generation"], str]:
    return {
        "generation": await llm.astream(
            state["docs"], config, callbacks=[stream_handler]
        )
    }


class RagGraph:
    graph: CompiledStateGraph

    @classmethod
    def from_config(
        cls,
        config: BackendConfig,
        vector_store: VectorStore,
        stream_handler: AsyncStreamingCallbackHandler,
    ) -> "RagGraph":
        graph = StateGraph(RagGraphState)

        graph.add_node("retrieve", partial(retrieve, vector_store.as_retriever()))
        graph.add_node("grade_docs", partial(grade_docs, config.llm))
        graph.add_node("generate", partial(generate, config.llm, stream_handler))

        graph.add_edge(START, "retrieve")
        graph.add_edge("retrieve", "grade_docs")
        graph.add_edge("grade_docs", "generate")
        graph.add_edge("generate", END)

        return graph.compile()


@tool
async def rag_tool(
    graph: RagGraph,
    input: Annotated[
        str, "A basic question from the user that you can answer quickly from memory."
    ],
) -> StructuredTool:
    """
    Answers questions about the most current fashion trends you have gathered from the internet
    in the past year. Use this tool when your user wants the most up-to-date advice and trends.
    """
    return graph.graph.ainvoke({"question": input})
