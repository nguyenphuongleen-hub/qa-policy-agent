import json
from qa_policy_agent.agent.state import AgentState
from qa_policy_agent.llm.provider import get_chat_model
from qa_policy_agent.llm.prompts.classification import CLASSIFICATION_SYSTEM_PROMPT


async def classify_request(state: AgentState) -> dict:
    llm = get_chat_model()
    response = await llm.ainvoke([
        {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
        {"role": "user", "content": state["question"]},
    ])
    classification = json.loads(response.content)
    return {"classification": classification}