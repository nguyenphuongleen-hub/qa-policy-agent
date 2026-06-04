import re
from qa_policy_agent.agent.state import AgentState
from qa_policy_agent.llm.provider import get_chat_model
from qa_policy_agent.llm.prompts.generation import GENERATION_SYSTEM_PROMPT


async def generate_answer(state: AgentState) -> dict:
    llm = get_chat_model()

    context_parts = []
    for chunk in state["relevant_chunks"]:
        context_parts.append(
            f"[{chunk['source_file']} | {chunk['section']}]\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    system = GENERATION_SYSTEM_PROMPT.format(context=context)
    response = await llm.ainvoke([
        {"role": "system", "content": system},
        {"role": "user", "content": state["question"]},
    ])

    # Extract citations
    citation_pattern = r"\[Source:\s*(.+?)\s*\|\s*(.+?)\]"
    citations = [
        {"source_file": m[0].strip(), "section": m[1].strip()}
        for m in re.findall(citation_pattern, response.content)
    ]

    return {
        "answer": response.content,
        "citations": citations,
        "retry_count": state.get("retry_count", 0) + 1,
    }