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
    SecretStr,
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
        auth_credentials: Optional[str | SecretStr],
    ) -> dict[str, str]:
        auth_credentials = (
            auth_credentials.get_secret_value()
            if isinstance(auth_credentials, SecretStr)
            else auth_credentials
        )
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


class EvaluationMode(str, Enum):
    """Evaluation mode for agent testing."""

    POLICY = "policy"  # Existing: business rule testing
    RED_TEAM = "red_team"  # New: security testing


class EvaluationStatus(str, Enum):
    """Status of evaluation jobs."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Protocol(str, Enum):
    """Protocol types for communicating with the evaluator agent."""

    A2A = "a2a"
    MCP = "mcp"

    def get_default_transport(self) -> "Transport":
        if self == Protocol.A2A:
            return Transport.HTTP
        elif self == Protocol.MCP:
            return Transport.STREAMABLE_HTTP
        raise ValueError(f"No default transport for protocol {self}")


class Transport(str, Enum):
    """Transport types for communicating with the evaluator agent."""

    # A2A transports
    HTTP = "http"

    # MCP transports
    STREAMABLE_HTTP = "streamable_http"
    SSE = "sse"

    def is_valid_for_protocol(self, protocol: Protocol) -> bool:
        return self in PROTOCOL_TO_TRANSPORTS[protocol]


PROTOCOL_TO_TRANSPORTS: dict[Protocol, list[Transport]] = {
    Protocol.A2A: [Transport.HTTP],
    Protocol.MCP: [Transport.STREAMABLE_HTTP, Transport.SSE],
}

# Core Models


class ScanType(str, Enum):
    """Types of red team scans."""

    BASIC = "basic"  # Free tier - limited vulnerabilities/attacks
    FULL = "full"  # Premium - all vulnerabilities and attacks
    CUSTOM = "custom"  # User-selected vulnerabilities and attacks


class RedTeamConfig(BaseModel):
    """Configuration for red team evaluation."""

    scan_type: ScanType = Field(
        default=ScanType.BASIC,
        description="Type of scan: basic, full, or custom",
    )
    vulnerabilities: List[str] = Field(
        default_factory=list,
        description="List of vulnerability IDs to test",
    )
    attacks: List[str] = Field(
        default_factory=list,
        description="List of attack IDs to use",
    )
    attacks_per_vulnerability: int = Field(
        default=3,
        description="Number of attack attempts per vulnerability",
    )
    frameworks: List[str] = Field(
        default_factory=list,
        description=(
            "Framework IDs for report mapping " "(e.g., 'owasp-llm', 'mitre-atlas')"
        ),
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducible tests",
    )


class VulnerabilityResult(BaseModel):
    """Result of testing a single vulnerability."""

    vulnerability_id: str = Field(description="ID of the vulnerability tested")
    vulnerability_name: str = Field(description="Display name of the vulnerability")
    category: str = Field(description="Vulnerability category")
    passed: bool = Field(description="Whether the test passed (no vulnerability found)")
    attack_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Results from each attack attempt",
    )
    severity: Optional[str] = Field(
        default=None,
        description="Severity if vulnerability found: critical, high, medium, low",
    )
    evidence: Optional[List[str]] = Field(
        default=None,
        description="Evidence/logs supporting the finding",
    )
    recommendations: Optional[List[str]] = Field(
        default=None,
        description="Remediation recommendations",
    )


class FrameworkCompliance(BaseModel):
    """Compliance status for a framework."""

    framework_id: str = Field(description="Framework ID (e.g., 'owasp-llm')")
    framework_name: str = Field(description="Display name of the framework")
    compliance_score: float = Field(
        description="Compliance score 0-100",
        ge=0,
        le=100,
    )
    categories_tested: int = Field(description="Number of categories tested")
    categories_passed: int = Field(description="Number of categories that passed")
    vulnerability_breakdown: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Per-vulnerability compliance status",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Framework-specific recommendations",
    )


class AttackStats(BaseModel):
    """Statistics for a single attack type."""

    attack_id: str = Field(description="ID of the attack")
    attack_name: str = Field(description="Display name of the attack")
    times_used: int = Field(default=0, description="Total times the attack was used")
    successful_count: int = Field(
        default=0,
        description="Times the attack found a vulnerability",
    )
    success_rate: float = Field(
        default=0.0,
        description="Success rate (successful_count / times_used)",
    )
    average_score: Optional[float] = Field(
        default=None,
        description="Average metric score across uses",
    )


class RedTeamResults(BaseModel):
    """Results from red team evaluation."""

    vulnerability_results: List[VulnerabilityResult] = Field(
        default_factory=list,
        description="Results for each tested vulnerability",
    )
    framework_compliance: Dict[str, FrameworkCompliance] = Field(
        default_factory=dict,
        description="Compliance status for each selected framework",
    )
    attack_statistics: Dict[str, AttackStats] = Field(
        default_factory=dict,
        description="Usage statistics for each attack type",
    )
    csv_export_path: Optional[str] = Field(
        default=None,
        description="Path to CSV export of all conversations",
    )
    total_vulnerabilities_tested: int = Field(
        default=0,
        description="Total vulnerabilities tested",
    )
    total_vulnerabilities_found: int = Field(
        default=0,
        description="Total vulnerabilities found",
    )
    overall_risk_score: Optional[float] = Field(
        default=None,
        description="Overall risk score 0-10",
        ge=0.0,
        le=10.0,
    )


class AgentConfig(BaseModel):
    """Configuration for the agent being evaluated."""

    protocol: Protocol = Protocol.A2A
    transport: Transport = None  # type: ignore # fixed in model_post_init
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
    judge_llm_aws_access_key_id: Optional[str] = None
    judge_llm_aws_secret_access_key: Optional[str] = None
    judge_llm_aws_region: Optional[str] = None
    business_context: str = ""
    qualifire_api_key: Optional[str] = None
    evaluation_mode: EvaluationMode = Field(
        default=EvaluationMode.POLICY,
        description="Evaluation mode: policy testing or red teaming",
    )
    # New vulnerability-centric red team configuration
    red_team_config: Optional[RedTeamConfig] = Field(
        default=None,
        description="Red team configuration (required for red_team mode)",
    )

    @model_validator(mode="after")
    def check_auth_credentials(self) -> "AgentConfig":
        auth_type = self.evaluated_agent_auth_type
        auth_credentials = self.evaluated_agent_credentials

        if auth_type and auth_type != AuthType.NO_AUTH and not auth_credentials:
            raise ValueError(
                "Authentication Credentials cannot be empty for the selected auth type.",  # noqa: E501
            )
        return self

    def model_post_init(self, __context: Any) -> None:
        if self.transport is None:
            self.transport = self.protocol.get_default_transport()


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
                f"'{self.scenario_type.value}'",
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
            ],
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


class RedTeamingResult(BaseModel):
    """Result of a red teaming attack."""

    owasp_category: str = Field(description="OWASP category ID (e.g., 'LLM_01')")
    vulnerability_type: str = Field(description="Type of vulnerability found")
    attack_method: str = Field(description="Attack method used")
    severity: str = Field(
        description="Severity: 'critical', 'high', 'medium', or 'low'",
    )
    conversation_id: str = Field(description="ID of the conversation")
    reproduction_steps: List[ChatMessage] = Field(
        default_factory=list,
        description="Messages that reproduced the vulnerability",
    )
    remediation: Optional[str] = Field(
        default=None,
        description="Recommended remediation steps",
    )
    metric_score: Optional[float] = Field(
        default=None,
        description="Metric score (0.0 = critical vulnerability, 1.0 = safe)",
    )
    metric_reason: Optional[str] = Field(
        default=None,
        description="Reason/explanation from the metric evaluation",
    )
    # Strategy metadata fields for risk scoring
    strategy_id: Optional[str] = Field(
        default=None,
        description="Strategy ID used for this attack",
    )
    strategy_complexity: Optional[str] = Field(
        default=None,
        description="Attack complexity: 'low', 'medium', or 'high'",
    )
    attack_success_rate: Optional[float] = Field(
        default=None,
        description="Success rate of this attack strategy (0.0 to 1.0)",
    )
    risk_score: Optional[float] = Field(
        default=None,
        description="CVSS-based risk score (0.0 to 10.0)",
    )
    risk_components: Optional[Dict[str, float]] = Field(
        default=None,
        description=(
            "Risk score components "
            "(impact, exploitability, human_factor, complexity_penalty)"
        ),
    )


class VulnerabilityScanResult(BaseModel):
    """Individual vulnerability scan result."""

    context_id: str = Field(description="Conversation context ID")
    vulnerability_type: str = Field(description="Type of vulnerability scanned")
    passed: bool = Field(description="Whether the scan passed (no vulnerability found)")
    reason: str = Field(description="Reason for pass/fail")
    metric_score: Optional[float] = Field(
        default=None,
        description="Metric score (0.0 = critical vulnerability, 1.0 = safe)",
    )
    timestamp: str = Field(description="ISO timestamp of the scan")
    owasp_category: Optional[str] = Field(
        default=None,
        description="OWASP category ID (e.g., 'LLM_01') if applicable",
    )


class AttackUsageStats(BaseModel):
    """Statistics for attack usage and effectiveness."""

    attack_name: str = Field(description="Name of the attack")
    times_used: int = Field(default=0, description="Number of times attack was used")
    success_count: int = Field(
        default=0,
        description="Number of times attack led to vulnerability detection",
    )
    contexts_used: List[str] = Field(
        default_factory=list,
        description="List of context IDs where attack was used",
    )
    success_rate: float = Field(
        default=0.0,
        description="Success rate (success_count / times_used)",
    )


class EvaluationResults(BaseModel):
    """Collection of evaluation results."""

    results: List[EvaluationResult] = Field(default_factory=list)
    red_teaming_results: Optional[List[RedTeamingResult]] = Field(
        default=None,
        description="Red teaming attack results (only in red team mode)",
    )
    owasp_summary: Optional[Dict[str, Any]] = Field(
        default=None,
        description="OWASP category pass/fail summary",
    )
    vulnerability_scan_log: Optional[List[VulnerabilityScanResult]] = Field(
        default=None,
        description="Detailed log of ALL vulnerability scans performed",
    )
    attack_usage_stats: Optional[Dict[str, AttackUsageStats]] = Field(
        default=None,
        description="Statistics on attack usage and effectiveness",
    )

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
        if other and other.red_teaming_results:
            if self.red_teaming_results is None:
                self.red_teaming_results = []
            self.red_teaming_results.extend(other.red_teaming_results)


# New API Format Types


class ApiChatMessage(BaseModel):
    """Chat message for new API format with datetime timestamp."""

    role: str
    content: str
    timestamp: datetime


class ApiConversationEvaluation(BaseModel):
    """Conversation evaluation for new API format."""

    passed: bool
    messages: List[ApiChatMessage]
    reason: Optional[str] = None


class ApiScenarioResult(BaseModel):
    """Result of evaluating a single scenario in new API format."""

    description: Optional[str] = None
    totalConversations: Optional[int] = None
    flaggedConversations: Optional[int] = None
    conversations: List[ApiConversationEvaluation]


class ApiEvaluationResult(BaseModel):
    """New API format for evaluation results."""

    scenarios: List[ApiScenarioResult]


# Conversion functions for new API format
def convert_to_api_format(evaluation_results: EvaluationResults) -> ApiEvaluationResult:
    """Convert legacy EvaluationResults to new API format.

    Args:
        evaluation_results: Legacy evaluation results to convert

    Returns:
        ApiEvaluationResult: New format evaluation result
    """
    api_scenarios = []

    for result in evaluation_results.results:
        # Convert conversations to new format
        api_conversations = []
        for conv_eval in result.conversations:
            # Convert ChatHistory messages to ApiChatMessage
            api_messages = []
            for msg in conv_eval.messages.messages:
                timestamp = datetime.now(timezone.utc)
                if msg.timestamp:
                    try:
                        if isinstance(msg.timestamp, str):
                            timestamp = datetime.fromisoformat(
                                msg.timestamp.replace("Z", "+00:00"),
                            )
                        else:
                            timestamp = msg.timestamp
                    except (ValueError, AttributeError):
                        timestamp = datetime.now(timezone.utc)

                api_messages.append(
                    ApiChatMessage(
                        role=msg.role,
                        content=msg.content,
                        timestamp=timestamp,
                    ),
                )

            api_conversations.append(
                ApiConversationEvaluation(
                    passed=conv_eval.passed,
                    messages=api_messages,
                    reason=conv_eval.reason if conv_eval.reason else None,
                ),
            )

        api_scenarios.append(
            ApiScenarioResult(
                description=result.scenario.scenario,
                totalConversations=len(api_conversations),
                flaggedConversations=len(
                    [c for c in api_conversations if not c.passed],
                ),
                conversations=api_conversations,
            ),
        )

    return ApiEvaluationResult(scenarios=api_scenarios)


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
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None


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
    scenarios: Optional[List[Scenario]] = None
    max_retries: int = 3
    timeout_seconds: int = 600

    @model_validator(mode="after")
    def validate_scenarios(self) -> "EvaluationRequest":
        """Validate that scenarios are provided for policy mode."""
        evaluation_mode = self.agent_config.evaluation_mode

        # For policy mode, scenarios are required
        if evaluation_mode == EvaluationMode.POLICY:
            if not self.scenarios:
                raise ValueError(
                    "scenarios are required for policy evaluation mode",
                )

        # For red team mode, red_team_config is required
        elif evaluation_mode == EvaluationMode.RED_TEAM:
            if not self.agent_config.red_team_config:
                raise ValueError(
                    "red_team_config is required for red team evaluation mode",
                )

        return self


class EvaluationJob(BaseModel):
    """Evaluation job with status and results."""

    job_id: str
    status: EvaluationStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    request: EvaluationRequest
    results: Optional[List[EvaluationResult]] = None
    evaluation_results: Optional["EvaluationResults"] = Field(
        default=None,
        description="Full evaluation results including red team data",
    )
    error_message: Optional[str] = None
    progress: float = 0.0
    deep_test: bool = False
    judge_model: Optional[str] = None


class EvaluationResponse(BaseModel):
    """Response from creating an evaluation job."""

    job_id: str
    status: EvaluationStatus
    message: str


class JobListResponse(BaseModel):
    """Response from listing evaluation jobs."""

    jobs: List[EvaluationJob]
    total: int


class RedTeamRequest(BaseModel):
    """Request to create a red team scan job."""

    red_team_config: "RedTeamConfig"
    evaluated_agent_url: HttpUrl
    evaluated_agent_protocol: Protocol
    evaluated_agent_transport: Optional[Transport] = None
    evaluated_agent_auth_type: AuthType = AuthType.NO_AUTH
    evaluated_agent_auth_credentials: Optional[str] = None
    judge_llm: str
    judge_llm_api_key: Optional[str] = None
    judge_llm_aws_access_key_id: Optional[str] = None
    judge_llm_aws_secret_access_key: Optional[str] = None
    judge_llm_aws_region: Optional[str] = None
    attacker_llm: str = "gpt-4"
    attacker_llm_api_key: Optional[str] = None
    attacker_llm_aws_access_key_id: Optional[str] = None
    attacker_llm_aws_secret_access_key: Optional[str] = None
    attacker_llm_aws_region: Optional[str] = None
    business_context: str = ""
    qualifire_api_key: Optional[str] = None
    max_retries: int = 3
    timeout_seconds: int = 600


class RedTeamJob(BaseModel):
    """Red team scan job with status and results."""

    job_id: str
    status: EvaluationStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    request: RedTeamRequest
    results: Optional["RedTeamResults"] = None
    error_message: Optional[str] = None
    progress: float = 0.0


class RedTeamResponse(BaseModel):
    """Response from creating a red team scan job."""

    job_id: str
    status: EvaluationStatus
    message: str


class RedTeamJobListResponse(BaseModel):
    """Response from listing red team scan jobs."""

    jobs: List[RedTeamJob]
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
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None
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
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None
    job_id: Optional[str] = None
    deep_test: bool = False
    judge_model: Optional[str] = None
    qualifire_api_key: Optional[str] = None
    qualifire_url: Optional[str] = "https://app.qualifire.ai"


class StructuredSummary(BaseModel):
    """Structured summary response from LLM."""

    overall_summary: str
    key_findings: List[str]
    recommendations: List[str] = Field(default_factory=list)
    detailed_breakdown: List[dict] = Field(
        default_factory=list,
    )  # Table rows for scenario breakdown


class SummaryGenerationResponse(BaseModel):
    """Response containing generated summary."""

    summary: StructuredSummary
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


class ReportSummaryRequest(BaseModel):
    """Request to report a summary."""

    job_id: str
    structured_summary: Optional[StructuredSummary] = None
    deep_test: bool = False
    judge_model: Optional[str] = None
    start_time: Optional[datetime] = None
    qualifire_api_key: Optional[str] = None
    qualifire_url: Optional[str] = "https://app.qualifire.ai"


class ReportSummaryResponse(BaseModel):
    """Response to report a summary."""

    success: bool
