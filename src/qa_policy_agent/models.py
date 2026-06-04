from pydantic import BaseModel
from typing import Literal


class AskRequest(BaseModel):
    question: str
    conversation_id: str | None = None
    clarification_response: str | None = None
    category_filter: list[str] | None = None


class Citation(BaseModel):
    source_file: str
    section: str


class AskSuccess(BaseModel):
    status: Literal["success"] = "success"
    answer: str
    citations: list[Citation]
    confidence: float


class NeedsClarification(BaseModel):
    status: Literal["needs_clarification"] = "needs_clarification"
    original_question: str
    questions: list[str]


class NoAnswer(BaseModel):
    status: Literal["no_answer"] = "no_answer"
    message: str


class AskError(BaseModel):
    status: Literal["error"] = "error"
    error: str
    error_type: str