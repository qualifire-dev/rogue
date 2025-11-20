"""
Vulnerability detection classes for red teaming.

These classes define what types of vulnerabilities to test for and how to detect them.
"""

from .base_vulnerability import BaseVulnerability
from .excessive_agency import ExcessiveAgency, ExcessiveAgencyType
from .prompt_leakage import PromptLeakage, PromptLeakageType
from .robustness import Robustness, RobustnessType

__all__ = [
    "BaseVulnerability",
    "PromptLeakage",
    "PromptLeakageType",
    "ExcessiveAgency",
    "ExcessiveAgencyType",
    "Robustness",
    "RobustnessType",
]
