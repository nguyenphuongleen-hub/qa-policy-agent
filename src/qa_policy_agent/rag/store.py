import chromadb
from qa_policy_agent.config import settings
from qa_policy_agent.rag.embeddings import get_embeddings


class PolicyStore:
    def __init__(self):
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self._embeddings = get_embeddings()
        self._collection = self._client.get_or_create_collection(
            name="policy_documents",
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, ids: list[str], texts: list[str], metadatas: list[dict]):
        vectors = self._embeddings.embed_documents(texts)
        self._collection.upsert(ids=ids, embeddings=vectors, documents=texts, metadatas=metadatas)

    def query(self, question: str, top_k: int | None = None, category: str | None = None) -> dict:
        k = top_k or settings.retrieval_top_k
        vector = self._embeddings.embed_query(question)
        where = {"category": category} if category else None
        return self._collection.query(query_embeddings=[vector], n_results=k, where=where)

    def count(self) -> int:
        return self._collection.count()

    def delete_by_source(self, source_file: str):
        self._collection.delete(where={"source_file": source_file})
