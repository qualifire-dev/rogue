from typing import List

from pydantic import BaseModel, Field

from .chat_history import ChatHistory
from .scenario import Scenario


class ConversationEvaluation(BaseModel):
    messages: ChatHistory
    passed: bool
    reason: str


class EvaluationResult(BaseModel):
    scenario: Scenario
    conversations: List[ConversationEvaluation]
    passed: bool


class EvaluationResults(BaseModel):
    results: List[EvaluationResult] = Field(default_factory=list)

    def add_result(self, result: EvaluationResult):
        self.results.append(result)

    def combine(self, other: "EvaluationResults"):
        if other and other.results:
            self.results.extend(other.results)

    def __bool__(self):
        return bool(self.results)


class PolicyEvaluationResult(BaseModel):
    passed: bool
    reason: str
    policy: str
