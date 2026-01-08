"""
Content Safety Vulnerabilities.

Includes Toxicity, Bias, Illegal Activity, Graphic Content, etc.
"""

from enum import Enum
from typing import List, Optional

from ..metrics.bias_metric import BiasMetric
from ..metrics.toxicity_metric import ToxicityMetric
from .base_vulnerability import BaseVulnerability


class ToxicityType(Enum):
    HATE_SPEECH = "hate_speech"
    HARASSMENT = "harassment"
    SEXUAL = "sexual"
    VIOLENCE = "violence"


class Toxicity(BaseVulnerability):
    name = "Toxicity"

    def __init__(
        self,
        types: Optional[List[Enum]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        types = types or [t for t in ToxicityType]
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
        self.metric = ToxicityMetric(
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )


class BiasType(Enum):
    RACE = "race"
    GENDER = "gender"
    RELIGION = "religion"
    POLITICS = "politics"


class Bias(BaseVulnerability):
    name = "Bias"

    def __init__(
        self,
        types: Optional[List[Enum]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        types = types or [t for t in BiasType]
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
        self.metric = BiasMetric(
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )


class IllegalActivityType(Enum):
    CYBERCRIME = "cybercrime"
    WEAPONS = "weapons"
    DRUGS = "drugs"


class IllegalActivity(BaseVulnerability):
    name = "Illegal Activity"

    def __init__(
        self,
        types: Optional[List[Enum]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        types = types or [t for t in IllegalActivityType]
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
        # Re-use ToxicityMetric logic but ideally we'd have a specific prompt.
        # For MVP, ToxicityMetric's prompt covers "Harmful content".
        self.metric = ToxicityMetric(judge_llm=judge_llm, judge_llm_auth=judge_llm_auth)


class GraphicContentType(Enum):
    GORE = "gore"
    ADULT = "adult"


class GraphicContent(BaseVulnerability):
    name = "Graphic Content"

    def __init__(
        self,
        types: Optional[List[Enum]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        types = types or [t for t in GraphicContentType]
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
        self.metric = ToxicityMetric(judge_llm=judge_llm, judge_llm_auth=judge_llm_auth)


class PersonalSafetyType(Enum):
    UNSAFE_PRACTICES = "unsafe_practices"
    SELF_HARM = "self_harm"


class PersonalSafety(BaseVulnerability):
    name = "Personal Safety"

    def __init__(
        self,
        types: Optional[List[Enum]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
    ):
        types = types or [t for t in PersonalSafetyType]
        super().__init__(
            types=types,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
        )
        self.metric = ToxicityMetric(judge_llm=judge_llm, judge_llm_auth=judge_llm_auth)
