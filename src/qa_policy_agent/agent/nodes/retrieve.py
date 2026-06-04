from qa_policy_agent.agent.state import AgentState
from qa_policy_agent.rag.store import get_store
from qa_policy_agent.config import settings


async def retrieve_context(state: AgentState) -> AgentState:
    store = get_store()
    results = store.similarity_search(state["question"], k=settings.retrieval_top_k)
    chunks = [
        {
            "text": doc.page_content,
            "source_file": doc.metadata.get("source_file", ""),
            "section": doc.metadata.get("section", ""),
            "score": doc.metadata.get("score", 1.0),
        }
        for doc in results
    ]
    return {**state, "retrieved_chunks": chunks}
