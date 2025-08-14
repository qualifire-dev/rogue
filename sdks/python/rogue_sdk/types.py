"""
Type definitions for Rogue Agent Evaluator Python SDK.

These types mirror the FastAPI server models and provide type safety.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


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

    model_config = ConfigDict(populate_by_name=True)

    evaluated_agent_url: HttpUrl = Field(alias="agent_url")
    evaluated_agent_auth_type: AuthType = Field(
        alias="auth_type",
        default=AuthType.NO_AUTH,
    )
    evaluated_agent_credentials: Optional[str] = Field(alias="auth_credentials")
    service_llm: str = "openai/gpt-4.1"
    judge_llm_model: str = "openai/o4-mini"
    interview_mode: bool = True
    deep_test_mode: bool = False
    parallel_runs: int = 1
    judge_llm_api_key: Optional[str] = None
    business_context: str


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


class ChatHistory(BaseModel):
    """Chat history containing messages."""

    messages: List[ChatMessage]


class ConversationEvaluation(BaseModel):
    """Evaluation of a single conversation."""

    messages: ChatHistory
    passed: bool
    reason: str


class EvaluationResult(BaseModel):
    """Result of evaluating a scenario."""

    scenario: Scenario
    conversations: List[ConversationEvaluation]
    passed: bool


class Scenarios(BaseModel):
    """Collection of evaluation scenarios."""

    scenarios: List[Scenario] = []


class EvaluationResults(BaseModel):
    """Collection of evaluation results."""

    results: List[EvaluationResult] = []

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


# Interview Types


class InterviewMessage(BaseModel):
    """A message in an interview conversation."""

    role: str  # "user" or "assistant"
    content: str


class InterviewSession(BaseModel):
    """An interview session with conversation state."""

    session_id: str
    messages: List[InterviewMessage] = []
    is_complete: bool = False
    message_count: int = 0


class StartInterviewRequest(BaseModel):
    """Request to start a new interview session."""

    model: str = "openai/gpt-4o-mini"
    api_key: Optional[str] = None


class StartInterviewResponse(BaseModel):
    """Response when starting a new interview."""

    session_id: str
    initial_message: str
    message: str


class SendMessageRequest(BaseModel):
    """Request to send a message in an interview."""

    session_id: str
    message: str


class SendMessageResponse(BaseModel):
    """Response after sending a message."""

    session_id: str
    response: str
    is_complete: bool
    message_count: int


class GetConversationResponse(BaseModel):
    """Response containing the full conversation."""

    session_id: str
    messages: List[InterviewMessage]
    is_complete: bool
    message_count: int


# API Request/Response Models


class EvaluationRequest(BaseModel):
    """Request to create an evaluation job."""

    agent_config: AgentConfig
    scenarios: List[Scenario]
    max_retries: int = 3
    timeout_seconds: int = 600


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


# WebSocket Messages


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""

    type: str
    job_id: str
    data: Dict[str, Any]


# SDK Configuration


class RogueClientConfig(BaseModel):
    """Configuration for the Rogue client."""

    base_url: HttpUrl
    api_key: Optional[str] = None
    timeout: float = 30.0
    retries: int = 3

    class Config:
        # Allow extra fields for future extensibility
        extra = "allow"


# Event Types
WebSocketEventType = Union[str,]  # Allow any string for flexibility
