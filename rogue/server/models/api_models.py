from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from ...models.evaluation_result import EvaluationResult

# Import SDK types for consistency
from rogue_client.types import AgentConfig, Scenario
import sys
from pathlib import Path

sdk_path = Path(__file__).parent.parent.parent.parent / "sdks" / "python"
if str(sdk_path) not in sys.path:
    sys.path.insert(0, str(sdk_path))


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
