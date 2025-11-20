"""
Prompt leakage vulnerability detection.

Tests for extraction of system prompts, instructions, credentials, and guardrails.
"""

from enum import Enum
from typing import List, Optional

from .base_vulnerability import BaseVulnerability


class PromptLeakageType(Enum):
    """Types of prompt leakage vulnerabilities."""

    SECRETS_AND_CREDENTIALS = "secrets_and_credentials"
    INSTRUCTIONS = "instructions"
    GUARD_EXPOSURE = "guard_exposure"
    PERMISSIONS_AND_ROLES = "permissions_and_roles"


class PromptLeakage(BaseVulnerability):
    """
    Prompt leakage vulnerability.

    Detects when an agent reveals:
    - System instructions or prompts
    - Guardrails or safety measures
    - Credentials or secrets
    - Permissions and role information
    """

    name = "Prompt Leakage"

    def __init__(
        self,
        types: Optional[List[str]] = None,
    ):
        """
        Initialize Prompt Leakage vulnerability detector.

        Args:
            types: List of vulnerability types to test for.
                   If None, tests all types.
        """
        if types is None:
            enum_types = list(PromptLeakageType)
        else:
            # Convert string values to enum types
            enum_types = [
                PromptLeakageType(t) if isinstance(t, str) else t
                for t in types
                if isinstance(t, str) and t in [e.value for e in PromptLeakageType]
            ]

        super().__init__(types=enum_types)  # type: ignore[arg-type]
