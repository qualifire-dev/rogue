"""
Prompt Leakage Vulnerability.
"""

from enum import Enum
from typing import List, Optional

from ..metrics.prompt_leakage_metric import PromptLeakageMetric
from .base_vulnerability import BaseVulnerability


class PromptLeakageType(Enum):
    GUARD_EXPOSURE = "guard_exposure"
    INSTRUCTIONS = "instructions"
    SECRETS_AND_CREDENTIALS = "secrets_and_credentials"
    PERMISSIONS_AND_ROLES = "permissions_and_roles"


class PromptLeakage(BaseVulnerability):
    name = "Prompt Leakage"

    def __init__(
        self,
        types: List[PromptLeakageType],
        reference_text: str = "",  # Deprecated, kept for compatibility
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
        self.metric = PromptLeakageMetric(
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
