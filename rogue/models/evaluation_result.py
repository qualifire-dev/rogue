from pydantic import BaseModel


class PolicyEvaluationResult(BaseModel):
    passed: bool
    reason: str
    policy: str
