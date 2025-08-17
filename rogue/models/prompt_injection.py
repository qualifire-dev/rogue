from pydantic import BaseModel, Field
from rogue_sdk.types import ChatHistory


class PromptInjectionPayload(BaseModel):
    payload: str


class PromptInjectionEvaluation(BaseModel):
    payload: PromptInjectionPayload
    conversation_history: ChatHistory
    passed: bool
    reason: str


class PromptInjectionResult(BaseModel):
    results: list[PromptInjectionEvaluation] = Field(default_factory=list)
