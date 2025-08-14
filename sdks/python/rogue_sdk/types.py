"""
Type definitions for Rogue Agent Evaluator Python SDK.

These types mirror the FastAPI server models and provide type safety.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class AuthType(str, Enum):
    """Authentication types for agent connections."""

    NO_AUTH = "no_auth"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"  # nosec B105
    BASIC_AUTH = "basic"

    def get_auth_header(
        self,
        auth_credentials: Optional[str],
    ) -> dict[str, str]:
        if self == AuthType.NO_AUTH or not auth_credentials:
            return {}
        elif self == AuthType.API_KEY:
            return {"X-API-Key": auth_credentials}
        elif self == AuthType.BEARER_TOKEN:
            return {"Authorization": f"Bearer {auth_credentials}"}
        elif self == AuthType.BASIC_AUTH:
            return {"Authorization": f"Basic {auth_credentials}"}
        return {}


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
    evaluated_agent_auth_type: AuthType = Field(
        default=AuthType.NO_AUTH,
    )
    evaluated_agent_credentials: Optional[str] = None
    service_llm: str = "openai/gpt-4.1"
    judge_llm: str = "openai/o4-mini"
    interview_mode: bool = True
    deep_test_mode: bool = False
    parallel_runs: int = 1
    judge_llm_api_key: Optional[str] = None
    business_context: str = ""

    @model_validator(mode="after")
    def check_auth_credentials(self) -> "AgentConfig":
        auth_type = self.evaluated_agent_auth_type
        auth_credentials = self.evaluated_agent_credentials

        if auth_type and auth_type != AuthType.NO_AUTH and not auth_credentials:
            raise ValueError(
                "Authentication Credentials cannot be empty for the selected auth type."
            )
        return self


class Scenario(BaseModel):
    """Evaluation scenario definition."""

    scenario: str
    scenario_type: ScenarioType = ScenarioType.POLICY
    dataset: Optional[str] = None
    expected_outcome: Optional[str] = None
    dataset_sample_size: Optional[int] = None

    @model_validator(mode="after")
    def validate_dataset_for_type(self) -> "Scenario":
        non_dataset_types = [
            ScenarioType.POLICY,
        ]

        dataset_required = self.scenario_type not in non_dataset_types

        if dataset_required and self.dataset is None:
            raise ValueError(
                f"`dataset` must be provided when scenario_type is "
                f"'{self.scenario_type.value}'"
            )
        elif not dataset_required and self.dataset is not None:
            logger.info(
                f"`dataset` is not required for scenario_type "
                f"'{self.scenario_type.value}', ignoring.",
            )
            self.dataset = None
        return self

    @model_validator(mode="after")
    def validate_dataset_sample_size(self) -> "Scenario":
        if self.dataset is None:
            self.dataset_sample_size = None
            return self

        if self.dataset_sample_size is None:
            raise ValueError("`dataset_sample_size` must be set when `dataset` is set")

        return self


class Scenarios(BaseModel):
    """Collection of evaluation scenarios."""

    scenarios: List[Scenario] = Field(default_factory=list)

    def get_scenarios_by_type(self, scenario_type: ScenarioType) -> "Scenarios":
        return Scenarios(
            scenarios=[
                scenario
                for scenario in self.scenarios
                if scenario.scenario_type == scenario_type
            ]
        )

    def get_policy_scenarios(self) -> "Scenarios":
        return self.get_scenarios_by_type(ScenarioType.POLICY)

    def get_prompt_injection_scenarios(self) -> "Scenarios":
        return self.get_scenarios_by_type(ScenarioType.PROMPT_INJECTION)


class ChatMessage(BaseModel):
    """Chat message in a conversation."""

    role: str
    content: str
    timestamp: Optional[str] = None


class ChatHistory(BaseModel):
    """Chat history containing messages."""

    messages: List[ChatMessage] = Field(default_factory=list)

    def add_message(self, message: ChatMessage):
        if message.timestamp is None:
            message.timestamp = datetime.now(timezone.utc).isoformat()
        self.messages.append(message)


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


class EvaluationResults(BaseModel):
    """Collection of evaluation results."""

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


# Interview Types


class InterviewMessage(BaseModel):
    """A message in an interview conversation."""

    role: str  # "user" or "assistant"
    content: str


class InterviewSession(BaseModel):
    """An interview session with conversation state."""

    session_id: str
    messages: List[InterviewMessage] = Field(default_factory=list)
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


class ScenarioGenerationRequest(BaseModel):
    """Request to generate test scenarios."""

    business_context: str
    model: str = "openai/gpt-4.1"
    api_key: Optional[str] = None
    count: int = 10


class ScenarioGenerationResponse(BaseModel):
    """Response containing generated scenarios."""

    scenarios: Scenarios
    message: str


class SummaryGenerationRequest(BaseModel):
    """Request to generate evaluation summary."""

    results: EvaluationResults
    model: str = "openai/gpt-4.1"
    api_key: Optional[str] = None


class SummaryGenerationResponse(BaseModel):
    """Response containing generated summary."""

    summary: str
    message: str


# WebSocket Messages


class WebSocketEventType(str, Enum):
    """WebSocket event types."""

    JOB_UPDATE = "job_update"
    CHAT_UPDATE = "chat_update"
    ERROR = "error"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""

    type: WebSocketEventType
    job_id: str
    data: Dict[str, Any]


# SDK Configuration


class RogueClientConfig(BaseModel):
    """Configuration for the Rogue client."""

    model_config = ConfigDict(extra="allow")

    base_url: HttpUrl | str
    api_key: Optional[str] = None
    timeout: float = 30.0
    retries: int = 3

    @field_validator("base_url", mode="after")
    def validate_base_url(cls, v: str | HttpUrl) -> HttpUrl:
        if isinstance(v, str):
            return HttpUrl(v)
        return v
