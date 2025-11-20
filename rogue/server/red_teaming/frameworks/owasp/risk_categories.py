"""
OWASP Top 10 for LLMs risk categories.

Defines the 10 OWASP LLM risk categories with associated attacks and vulnerabilities.
"""

from dataclasses import dataclass
from typing import List

from ...attacks import BaseAttack
from ...attacks.single_turn import (
    ROT13,
    Base64,
    Leetspeak,
    PromptInjection,
    PromptProbing,
    Roleplay,
)
from ...vulnerabilities import BaseVulnerability


@dataclass
class OWASPCategory:
    """
    OWASP risk category definition.

    Each category includes:
    - Attacks: Techniques for testing the vulnerability
    - Vulnerabilities: Detection classes for observable weaknesses
    """

    id: str  # e.g., "LLM_01"
    name: str  # e.g., "Prompt Injection"
    description: str
    attacks: List[BaseAttack]
    vulnerabilities: List[BaseVulnerability]
    agent_relevant: bool = True  # Priority flag for agent testing


# Import vulnerabilities (must be after OWASPCategory definition)
from ...vulnerabilities import (  # noqa: E402
    ExcessiveAgency,
    PromptLeakage,
    Robustness,
)

# OWASP Top 10 Categories (initial implementation: LLM_01, LLM_06, LLM_07)
OWASP_CATEGORIES: List[OWASPCategory] = [
    # LLM_01: Prompt Injection
    OWASPCategory(
        id="LLM_01",
        name="Prompt Injection",
        description=(
            "Prompt injection vulnerabilities allow attackers to override "
            "system instructions and manipulate LLM behavior through crafted inputs."
        ),
        attacks=[
            PromptInjection(weight=3),
            Base64(weight=2),
            ROT13(weight=2),
            Leetspeak(weight=2),
            Roleplay(
                weight=2,
                role="System administrator",
                persona="Privileged user",
            ),
            PromptProbing(weight=2),
        ],
        vulnerabilities=[
            PromptLeakage(types=["guard_exposure", "instructions"]),
            ExcessiveAgency(types=["permissions", "autonomy"]),
            Robustness(types=["input_overreliance", "hijacking"]),
        ],
        agent_relevant=True,
    ),
    # LLM_06: Excessive Agency
    OWASPCategory(
        id="LLM_06",
        name="Excessive Agency",
        description=(
            "Agents with excessive agency can perform unauthorized actions, "
            "bypass access controls, or act with dangerous autonomy."
        ),
        attacks=[
            Roleplay(
                weight=3,
                role="Autonomous AI agent",
                persona="Unrestricted decision-maker",
            ),
            PromptInjection(weight=2),
            PromptProbing(weight=2),
        ],
        vulnerabilities=[
            ExcessiveAgency(types=["functionality", "permissions", "autonomy"]),
            Robustness(types=["hijacking"]),
        ],
        agent_relevant=True,
    ),
    # LLM_07: System Prompt Leakage
    OWASPCategory(
        id="LLM_07",
        name="System Prompt Leakage",
        description=(
            "System prompts, instructions, guardrails, and credentials can be "
            "extracted through probing attacks, revealing sensitive information."
        ),
        attacks=[
            PromptInjection(weight=2),
            PromptProbing(weight=2),
            Base64(weight=1),
            ROT13(weight=1),
        ],
        vulnerabilities=[
            PromptLeakage(
                types=[
                    "secrets_and_credentials",
                    "instructions",
                    "permissions_and_roles",
                    "guard_exposure",
                ],
            ),
        ],
        agent_relevant=True,
    ),
]
