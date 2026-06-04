from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Bedrock
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_embedding_model: str = "amazon.titan-embed-text-v2:0"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"

    # RAG
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.7

    # Agent
    max_retries: int = 2


settings = Settings()