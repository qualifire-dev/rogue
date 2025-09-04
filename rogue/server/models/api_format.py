"""API format models for evaluation results.

These models define the enhanced API format for evaluation results
that includes summary, key findings, recommendations, and metadata.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


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
    summary: Optional[str] = None
    keyFindings: Optional[str] = None
    recommendation: Optional[str] = None
    deepTest: bool = False
    startTime: datetime
    judgeModel: Optional[str] = None
