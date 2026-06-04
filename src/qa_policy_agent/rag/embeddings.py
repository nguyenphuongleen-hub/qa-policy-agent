from functools import lru_cache
from langchain_aws import BedrockEmbeddings
from qa_policy_agent.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> BedrockEmbeddings:
    return BedrockEmbeddings(
        model_id=settings.bedrock_embedding_model,
        region_name=settings.aws_region,
    )
