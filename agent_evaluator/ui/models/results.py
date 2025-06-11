from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class A2AMessage(BaseModel):
    # Placeholder for A2A message structure
    content: str


class AgentResponse(BaseModel):
    # Placeholder for Agent response structure
    content: str


class EvaluationResult(BaseModel):
    criterion: str
    score: float
    max_score: float
    reasoning: str
    evidence: List[str]


class TestExecution(BaseModel):
    execution_id: str
    scenario_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: ExecutionStatus
    a2a_messages: List[A2AMessage]
    agent_responses: List[AgentResponse]
    evaluation_results: List[EvaluationResult]
