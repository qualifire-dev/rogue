from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from ...models.scenario import Scenario
from ...models.config import AgentConfig
from ...models.evaluation_result import EvaluationResult


class EvaluationRequest(BaseModel):
    agent_config: AgentConfig
    scenarios: List[Scenario]
    max_retries: int = 3
    timeout_seconds: int = 300


class EvaluationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationJob(BaseModel):
    job_id: str
    status: EvaluationStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    request: EvaluationRequest
    results: Optional[List[EvaluationResult]] = None
    error_message: Optional[str] = None
    progress: float = 0.0


class EvaluationResponse(BaseModel):
    job_id: str
    status: EvaluationStatus
    message: str


class JobListResponse(BaseModel):
    jobs: List[EvaluationJob]
    total: int


class WebSocketMessage(BaseModel):
    type: str
    job_id: str
    data: dict
