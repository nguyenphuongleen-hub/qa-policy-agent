import json
from qa_policy_agent.agent.state import AgentState
from qa_policy_agent.llm.provider import get_chat_model


VERIFY_PROMPT = """Verify the answer against source chunks. Check:
1. Every [Source: ...] citation references a real provided chunk
2. Factual claims in the answer exist in the cited source
3. No major claims are made without a citation

Source chunks:
{chunks}

Answer to verify:
{answer}

Return ONLY JSON (no markdown): {{"passed": bool, "issues": [...], "confidence": 0.0-1.0}}
"""


async def verify_answer(state: AgentState) -> dict:
    llm = get_chat_model()

    chunks_text = "\n---\n".join(
        f"[{c['source_file']} | {c['section']}]\n{c['text']}"
        for c in state["relevant_chunks"]
    )

    response = await llm.ainvoke([
        {"role": "system", "content": VERIFY_PROMPT.format(chunks=chunks_text, answer=state["answer"])},
        {"role": "user", "content": "Verify the answer."},
    ])

    verification = json.loads(response.content)
    return {"verification": verification}