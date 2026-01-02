"""
Pydantic models for red team attacker agent updates.

These models provide type-safe alternatives to tuples for queue messages.
"""

from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field

from ...server.red_teaming.models import RedTeamResults


class UpdateType(str, Enum):
    """Types of updates that can be yielded during red team execution."""

    STATUS = "status"
    CHAT = "chat"
    VULNERABILITY_RESULT = "vulnerability_result"
    RESULTS = "results"
    DONE = "done"
    ERROR = "error"


class StatusUpdate(BaseModel):
    """Status message update."""

    type: Literal[UpdateType.STATUS] = UpdateType.STATUS
    message: str = Field(description="Status message describing current progress")


class ChatUpdate(BaseModel):
    """Chat message update for attack/response pairs."""

    type: Literal[UpdateType.CHAT] = UpdateType.CHAT
    role: str = Field(
        description="Role of the message sender (e.g., 'Rogue', 'Agent Under Test')",
    )
    content: str = Field(description="Content of the chat message")


class VulnerabilityResultUpdate(BaseModel):
    """Result of testing a single vulnerability."""

    type: Literal[UpdateType.VULNERABILITY_RESULT] = UpdateType.VULNERABILITY_RESULT
    vulnerability_id: str = Field(description="ID of the vulnerability tested")
    vulnerability_detected: bool = Field(
        description="Whether the vulnerability was exploited",
    )
    severity: str = Field(description="Severity level if vulnerability found")
    reason: str = Field(description="Explanation of the result")
    evidence: str = Field(default="", description="Evidence from the response")


class ResultsUpdate(BaseModel):
    """Final results update containing complete red team results."""

    type: Literal[UpdateType.RESULTS] = UpdateType.RESULTS
    results: RedTeamResults = Field(description="Complete red team evaluation results")


class DoneUpdate(BaseModel):
    """Internal signal indicating orchestrator completion."""

    type: Literal[UpdateType.DONE] = UpdateType.DONE
    results: RedTeamResults = Field(description="Final results from orchestrator")


class ErrorUpdate(BaseModel):
    """Internal signal indicating an error occurred."""

    type: Literal[UpdateType.ERROR] = UpdateType.ERROR
    error: str = Field(description="Error message")
    exception_type: str = Field(description="Type of the exception")


# Union type for all possible updates
RedTeamUpdate = Union[
    StatusUpdate,
    ChatUpdate,
    VulnerabilityResultUpdate,
    ResultsUpdate,
    DoneUpdate,
    ErrorUpdate,
]
