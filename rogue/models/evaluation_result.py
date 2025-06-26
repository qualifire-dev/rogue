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

    @classmethod
    def combine(
        cls, *results: "EvaluationResults" | List["EvaluationResults"] | None
    ) -> "EvaluationResults":
        combined = EvaluationResults()
        for evaluation_result in results:
            if evaluation_result is None:
                continue

            if isinstance(evaluation_result, list):
                evaluation_result = cls.combine(*evaluation_result)

            combined.results.extend(evaluation_result.results)
        return combined


class PolicyEvaluationResult(BaseModel):
    passed: bool
    reason: str
    policy: str
