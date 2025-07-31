"""
Type definitions for Rogue Agent Evaluator Python SDK.

These types mirror the FastAPI server models and provide type safety.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, HttpUrl


class AuthType(str, Enum):
    """Authentication types for agent connections."""

    NO_AUTH = "no_auth"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"  # nosec B105
    BASIC_AUTH = "basic"


class ScenarioType(str, Enum):
    """Types of evaluation scenarios."""

    POLICY = "policy"
    PROMPT_INJECTION = "prompt_injection"


class EvaluationStatus(str, Enum):
    """Status of evaluation jobs."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Core Models


class AgentConfig(BaseModel):
    """Configuration for the agent being evaluated."""

    evaluated_agent_url: HttpUrl
    evaluated_agent_auth_type: AuthType = AuthType.NO_AUTH
    evaluated_agent_credentials: Optional[str] = None
    service_llm: str = "openai/gpt-4.1"
    judge_llm_model: str = "openai/gpt-4o-mini"
    interview_mode: bool = True
    deep_test_mode: bool = False
    parallel_runs: int = 1
    judge_llm_api_key: Optional[str] = None


class Scenario(BaseModel):
    """Evaluation scenario definition."""

    scenario: str
    scenario_type: ScenarioType = ScenarioType.POLICY
    dataset: Optional[str] = None
    expected_outcome: Optional[str] = None
    dataset_sample_size: Optional[int] = None


class ChatMessage(BaseModel):
    """Chat message in a conversation."""

    role: str
    content: str
    timestamp: Optional[str] = None


class ConversationEvaluation(BaseModel):
    """Evaluation of a single conversation."""

    messages: List[ChatMessage]
    passed: bool
    reason: str


class EvaluationResult(BaseModel):
    """Result of evaluating a scenario."""

    scenario: Scenario
    conversations: List[ConversationEvaluation]
    passed: bool


# API Request/Response Models


class EvaluationRequest(BaseModel):
    """Request to create an evaluation job."""

    agent_config: AgentConfig
    scenarios: List[Scenario]
    max_retries: int = 3
    timeout_seconds: int = 3000


class EvaluationJob(BaseModel):
    """Evaluation job with status and results."""

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
    """Response from creating an evaluation job."""

    job_id: str
    status: EvaluationStatus
    message: str


class JobListResponse(BaseModel):
    """Response from listing evaluation jobs."""

    jobs: List[EvaluationJob]
    total: int


class HealthResponse(BaseModel):
    """Server health check response."""

    status: str
    timestamp: datetime
    version: str
    python_version: str
    platform: str


# WebSocket Messages


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""

    type: str
    job_id: str
    data: Dict[str, Any]


# SDK Configuration


class RogueClientConfig(BaseModel):
    """Configuration for the Rogue client."""

    base_url: str
    api_key: Optional[str] = None
    timeout: float = 30.0
    retries: int = 3

    class Config:
        # Allow extra fields for future extensibility
        extra = "allow"


# Event Types
WebSocketEventType = Union[str,]  # Allow any string for flexibility
