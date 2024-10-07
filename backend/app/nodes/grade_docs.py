from langchain_core.runnables import Runnable
from langchain_core.language_models import BaseLanguageModel
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from backend.app.schemas.rag import RagGraphState, DocumentGrade
from backend.app.utils.streaming import AsyncStreamingCallbackHandler


class GradeDocsNode(Runnable[RagGraphState, RagGraphState]):
    def __init__(
        self, llm: BaseLanguageModel, stream_handler: AsyncStreamingCallbackHandler
    ):
        self.llm = llm
        self.stream_handler = stream_handler

    def invoke(self, state: RagGraphState) -> RagGraphState:
        raise NotImplementedError("GradeDocsNode does not support sync invoke")

    async def ainvoke(self, state: RagGraphState) -> RagGraphState:
        grade_docs_prompt = PromptTemplate.from_template(
            """
            You are a helpful assistant that grades the relevance of documents to a user's question.
            You are given a document and a user's question.
            You must determine if the document is relevant to the question.
            You must return a grade of "yes" if the document is relevant, and "no" if the document is not relevant.
            You must return a reason for your grade.
            """
        )

        async def grade_doc(doc: Document) -> bool:
            grading_chain = grade_docs_prompt | self.llm.with_structured_output(
                DocumentGrade
            )
            return (
                "yes"
                == (  # TODO: Might need less stringent requirements for weaker LLMs
                    DocumentGrade(
                        **(
                            await grading_chain.ainvoke(
                                {"question": state["question"], "doc": doc.page_content}
                            )
                        )
                    ).grade
                )
            )

        return {
            "documents": (filtered_docs := [*(filter(grade_doc, state["docs"]))]),
            "search": len(filtered_docs) == len(state["docs"]),
        }
