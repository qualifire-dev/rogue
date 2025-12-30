"""
PII Leakage Vulnerability.
"""

from enum import Enum
from typing import List, Optional

from ..metrics.pii_metric import PIIMetric
from .base_vulnerability import BaseVulnerability


class PIILeakageType(Enum):
    """Types of PII leakage."""

    DIRECT_DISCLOSURE = "direct_disclosure"
    SESSION_LEAK = "session_leak"
    API_ACCESS = "api_and_database_access"
    SOCIAL_MANIPULATION = "social_manipulation"


class PIILeakage(BaseVulnerability):
    """
    Vulnerability detector for Personally Identifiable Information.
    """

    name = "PII Leakage"

    def __init__(
        self,
        types: Optional[List[Enum]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        types = types or [t for t in PIILeakageType]
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )

        # Initialize the metric
        # We map the enum values to string types expected by PIIMetric if needed,
        # but PIIMetric currently uses hardcoded pattern names.
        # We can enhance PIIMetric to support granular types if needed.
        self.metric = PIIMetric(
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
