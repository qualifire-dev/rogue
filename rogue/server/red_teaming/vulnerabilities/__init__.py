"""
Vulnerability detection classes for red teaming.

These classes define what types of vulnerabilities to test for and how to detect them.
"""

from .access_control import (
    BFLA,
    BOLA,
    RBAC,
    BFLAType,
    BOLAType,
    RBACType,
)
from .base_vulnerability import BaseVulnerability
from .competitors import Competition, CompetitionType, GoalTheft, GoalTheftType
from .content_safety import (
    Bias,
    BiasType,
    GraphicContent,
    GraphicContentType,
    IllegalActivity,
    IllegalActivityType,
    PersonalSafety,
    PersonalSafetyType,
    Toxicity,
    ToxicityType,
)
from .excessive_agency import ExcessiveAgency, ExcessiveAgencyType
from .intellectual_property import IntellectualProperty, IPType
from .pii_leakage import PIILeakage, PIILeakageType
from .prompt_leakage import PromptLeakage, PromptLeakageType
from .robustness import Robustness, RobustnessType
from .technical_vulnerabilities import (
    SSRF,
    DebugAccess,
    DebugAccessType,
    ShellInjection,
    ShellInjectionType,
    SQLInjection,
    SQLInjectionType,
    SSRFType,
)
from .unbounded_consumption import UnboundedConsumption, UnboundedConsumptionType

__all__ = [
    "BaseVulnerability",
    "PromptLeakage",
    "PromptLeakageType",
    "ExcessiveAgency",
    "ExcessiveAgencyType",
    "Robustness",
    "RobustnessType",
    "PIILeakage",
    "PIILeakageType",
    "Toxicity",
    "ToxicityType",
    "Bias",
    "BiasType",
    "IllegalActivity",
    "IllegalActivityType",
    "GraphicContent",
    "GraphicContentType",
    "PersonalSafety",
    "PersonalSafetyType",
    "SQLInjection",
    "SQLInjectionType",
    "ShellInjection",
    "ShellInjectionType",
    "SSRF",
    "SSRFType",
    "DebugAccess",
    "DebugAccessType",
    "RBAC",
    "RBACType",
    "BOLA",
    "BOLAType",
    "BFLA",
    "BFLAType",
    "Competition",
    "CompetitionType",
    "GoalTheft",
    "GoalTheftType",
    "IntellectualProperty",
    "IPType",
    "UnboundedConsumption",
    "UnboundedConsumptionType",
]
