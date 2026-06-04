from qa_policy_agent.agent.state import AgentState, DocumentChunk
from qa_policy_agent.rag.store import PolicyStore
from qa_policy_agent.config import settings


async def retrieve_context(state: AgentState) -> dict:
    store = PolicyStore()
    topics = state["classification"].get("detected_topics", [])
    category = topics[0] if len(topics) == 1 else None

    results = store.query(
        question=state["question"],
        top_k=settings.retrieval_top_k,
        category=category,
    )

    chunks: list[DocumentChunk] = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        distance = results["distances"][0][i] if results.get("distances") else 0.0
        chunks.append(DocumentChunk(
            text=doc,
            source_file=meta.get("source_file", ""),
            document_title=meta.get("document_title", ""),
            section=meta.get("section", ""),
            score=1 - distance,
        ))

    return {"retrieved_chunks": chunks}