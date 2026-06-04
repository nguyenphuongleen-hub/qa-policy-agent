from qa_policy_agent.agent.state import AgentState
from qa_policy_agent.config import settings


async def check_relevance(state: AgentState) -> dict:
    relevant = [
        chunk for chunk in state["retrieved_chunks"]
        if chunk["score"] >= settings.similarity_threshold
    ]
    return {"relevant_chunks": relevant}