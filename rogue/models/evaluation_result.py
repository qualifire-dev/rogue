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

    def add_result(self, new_result: EvaluationResult):
        for result in self.results:
            if result.scenario.scenario == new_result.scenario.scenario:
                result.conversations.extend(new_result.conversations)
                result.passed = result.passed and new_result.passed
                return
        self.results.append(new_result)

    def combine(self, other: "EvaluationResults"):
        if other and other.results:
            for result in other.results:
                self.add_result(result)

    def __bool__(self):
        return bool(self.results)


class PolicyEvaluationResult(BaseModel):
    passed: bool
    reason: str
    policy: str
