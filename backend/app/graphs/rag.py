from functools import partial
from typing import Annotated, Literal, TypedDict, Optional, Union
import operator

from pydantic import BaseModel

from langchain.tools import StructuredTool
from langchain.prompts import PromptTemplate
from langchain_core.messages import ToolMessage, HumanMessage
from langchain_core.language_models import BaseLanguageModel
from langgraph.graph import StateGraph, START, END
from langchain.schema import BaseMessage
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langgraph.graph.state import CompiledStateGraph
from langchain_community.vectorstores import VectorStore
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableConfig


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
    llm: BaseLanguageModel, state: RagGraphState, config: RunnableConfig
) -> dict[Literal["generation"], str]:
    return {"generation": await llm.astream(state["docs"], config)}


class RagGraph:
    graph: CompiledStateGraph

    @classmethod
    def from_dependencies(
        cls,
        llm: BaseLanguageModel,
        vector_store: VectorStore,
    ) -> "RagGraph":
        graph = StateGraph(RagGraphState)

        graph.add_node("retrieve", partial(retrieve, vector_store.as_retriever()))
        graph.add_node("grade_docs", partial(grade_docs, llm))
        graph.add_node("generate", partial(generate, llm))

        graph.add_edge(START, "retrieve")
        graph.add_edge("retrieve", "grade_docs")
        graph.add_edge("grade_docs", "generate")
        graph.add_edge("generate", END)

        return graph.compile()