from qa_policy_agent.agent.state import AgentState
from qa_policy_agent.llm.provider import get_llm
from qa_policy_agent.llm.prompts.classification import CLASSIFICATION_SYSTEM_PROMPT


async def classify_request(state: AgentState) -> AgentState:
    llm = get_llm()
    response = await llm.ainvoke([
        {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
        {"role": "user", "content": state["question"]},
    ])
    text = response.content.strip().lower()

    if "block" in text:
        decision = "block"
        reason = "Câu hỏi vi phạm chính sách."
    elif "fallback" in text:
        decision = "fallback"
        reason = "Ngoài phạm vi."
    else:
        decision = "answer"
        reason = ""

    return {**state, "classification": {"decision": decision, "reason": reason}}
