import json
import logging

import boto3

from qa_policy_agent.config import settings

logger = logging.getLogger(__name__)


class BedrockEmbeddings:
    """
    AWS Bedrock Titan Embed V2 client.

    """

    def __init__(self) -> None:
        session = boto3.Session(
            region_name=settings.aws_region,
            profile_name=settings.aws_profile,
        )
        self.client = session.client("bedrock-runtime")
        self.model_id = settings.bedrock_embedding_model
        self.dimensions = settings.embedding_dimensions

    def embed_text(self, text: str) -> list[float]:
        """Embed 1 đoạn text → vector."""
        body = json.dumps({
            "inputText": text,
            "dimensions": self.dimensions,
            "normalize": True,
        })
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        return result["embedding"]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed nhiều text. Gọi tuần tự vì Titan không hỗ trợ batch.
        """
        embeddings = []
        for i, text in enumerate(texts):
            logger.debug(f"Embedding {i+1}/{len(texts)}...")
            embeddings.append(self.embed_text(text))
        return embeddings
