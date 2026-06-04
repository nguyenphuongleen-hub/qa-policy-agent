from typing import TypedDict


class DocumentChunk(TypedDict):
    text: str
    source_file: str
    document_title: str
    section: str
    score: float


class ClassificationResult(TypedDict):
    request_type: str   # policy_question | unsafe | out_of_scope | ambiguous
    decision: str       # continue | clarify | block | fallback
    detected_topics: list[str]
    block_reason: str | None
    reason: str


class VerificationResult(TypedDict):
    passed: bool
    issues: list[str]
    confidence: float


class AgentState(TypedDict):
    question: str
    conversation_history: list[dict]
    classification: ClassificationResult
    retrieved_chunks: list[DocumentChunk]
    relevant_chunks: list[DocumentChunk]
    answer: str
    citations: list[dict]
    verification: VerificationResult
    retry_count: int
    error: str | None