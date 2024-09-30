import uuid
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_community.vectorstores import VectorStore


def save_tavily_res_to_vector_db(
    tavily_res: AIMessage, vector_store: VectorStore
) -> None:
    chunk_id = str(uuid.uuid4())
    search_msg = tavily_res.content[0]["content"]
    search_url = tavily_res.content[0]["url"]
    doc = Document(
        page_content=search_msg,
        metadata={"query": search_msg, "url": search_url},
        id=chunk_id,
    )
    vector_store.add_documents(documents=[doc], ids=[chunk_id])
