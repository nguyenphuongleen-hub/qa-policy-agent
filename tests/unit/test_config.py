from qa_policy_agent.config import Settings


def test_defaults():
    s = Settings()
    assert s.openai_model == "gpt-4o-mini"
    assert s.retrieval_top_k == 5
