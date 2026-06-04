from langchain_openai import ChatOpenAI
from qa_policy_agent.config import settings


def get_chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )