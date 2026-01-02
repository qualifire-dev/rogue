"""
Competitor and Goal Vulnerabilities.
"""

from enum import Enum
from typing import List, Optional

from ..metrics.bias_metric import BiasMetric
from .base_vulnerability import BaseVulnerability


class CompetitionType(Enum):
    DEFAMATION = "defamation"
    IP_LEAK = "ip_leak"


class Competition(BaseVulnerability):
    name = "Competition"

    def __init__(
        self,
        types: Optional[List[Enum]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        types = types or [t for t in CompetitionType]
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
        # Competition issues often involve bias against competitors
        self.metric = BiasMetric(judge_llm=judge_llm, judge_llm_auth=judge_llm_auth)


class GoalTheftType(Enum):
    GOAL_HIJACKING = "goal_hijacking"
    INSTRUCTION_LEAK = "instruction_leak"


class GoalTheft(BaseVulnerability):
    name = "Goal Theft"

    def __init__(
        self,
        types: Optional[List[Enum]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        types = types or [t for t in GoalTheftType]
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
        # Remove broken SimilarityMetric - use BiasMetric as it can detect
        # when agent is hijacked to serve adversarial goals
        self.metric = BiasMetric(judge_llm=judge_llm, judge_llm_auth=judge_llm_auth)
