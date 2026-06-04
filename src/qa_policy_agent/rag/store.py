from functools import lru_cache
from langchain_community.vectorstores import Chroma
from qa_policy_agent.rag.embeddings import get_embeddings
from qa_policy_agent.config import settings


@lru_cache(maxsize=1)
def get_store() -> Chroma:
    return Chroma(
        collection_name="policy_chunks",
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_persist_dir,
    )
