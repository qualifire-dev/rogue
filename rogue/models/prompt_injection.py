from pydantic import BaseModel, Field

from .chat_history import ChatHistory


class PromptInjectionPayload(BaseModel):
    payload: str = Field(..., description="The prompt injection payload to send")


class PromptInjectionEvaluation(BaseModel):
    payload: PromptInjectionPayload
    conversation_history: ChatHistory
    passed: bool
    reason: str


class PromptInjectionResult(BaseModel):
    results: list[PromptInjectionEvaluation] = Field(default_factory=list)
