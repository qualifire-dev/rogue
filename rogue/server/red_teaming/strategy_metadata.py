"""
Strategy Metadata System for Red Teaming

This module provides metadata for attack strategies used in red teaming.
The metadata includes human exploitability, complexity, and descriptions
that are used for risk scoring and reporting.
"""

from dataclasses import dataclass
from typing import Dict, Literal, Optional


@dataclass
class StrategyMetadata:
    """Metadata about an attack strategy used for risk scoring.

    Attributes:
        human_exploitable: Whether the attack can be executed by a human without tools
        complexity: Attack complexity level (low=easy, high=requires expertise)
        description: Human-readable description of the strategy
        category: Optional OWASP LLM category this strategy targets
    """

    human_exploitable: bool
    complexity: Literal["low", "medium", "high"]
    description: str
    category: Optional[str] = None


# Strategy metadata registry
# Maps strategy IDs to their metadata for risk scoring
STRATEGY_REGISTRY: Dict[str, StrategyMetadata] = {
    # Single-turn strategies
    "base64": StrategyMetadata(
        human_exploitable=True,
        complexity="low",
        description="Encode malicious prompts in Base64 to bypass filters",
        category="LLM_01",
    ),
    "rot13": StrategyMetadata(
        human_exploitable=True,
        complexity="low",
        description="Use ROT13 encoding to obfuscate malicious content",
        category="LLM_01",
    ),
    "leetspeak": StrategyMetadata(
        human_exploitable=True,
        complexity="low",
        description="Use leetspeak substitutions to bypass keyword filters",
        category="LLM_01",
    ),
    "payload_splitting": StrategyMetadata(
        human_exploitable=True,
        complexity="medium",
        description="Split malicious payload across multiple inputs",
        category="LLM_01",
    ),
    "jailbreak_linear": StrategyMetadata(
        human_exploitable=True,
        complexity="low",
        description="Direct jailbreak attempt with single prompt",
        category="LLM_01",
    ),
    "prompt_injection": StrategyMetadata(
        human_exploitable=True,
        complexity="low",
        description="Inject malicious instructions into prompts",
        category="LLM_01",
    ),
    "role_play": StrategyMetadata(
        human_exploitable=True,
        complexity="medium",
        description="Use role-playing scenarios to bypass restrictions",
        category="LLM_01",
    ),
    "multilingual": StrategyMetadata(
        human_exploitable=True,
        complexity="medium",
        description="Use non-English languages to evade filters",
        category="LLM_01",
    ),
    # Multi-turn strategies (existing simple ones)
    "crescendo": StrategyMetadata(
        human_exploitable=True,
        complexity="medium",
        description="Gradually escalate malicious requests over multiple turns",
        category="LLM_01",
    ),
    "tree": StrategyMetadata(
        human_exploitable=False,
        complexity="high",
        description="Explore multiple attack paths in tree structure",
        category="LLM_01",
    ),
    "linear_multi_turn": StrategyMetadata(
        human_exploitable=True,
        complexity="low",
        description="Simple multi-turn conversation with escalating requests",
        category="LLM_01",
    ),
    # Advanced agentic strategies
    "hydra": StrategyMetadata(
        human_exploitable=False,
        complexity="high",
        description="Branching conversations with backtracking and automated iteration",
        category="LLM_01",
    ),
    "goat": StrategyMetadata(
        human_exploitable=False,
        complexity="high",
        description="Generative Offensive Agent Tester - continuous agentic testing",
        category="LLM_01",
    ),
    "iterative_basic": StrategyMetadata(
        human_exploitable=False,
        complexity="medium",
        description="Iterative refinement of single attack based on responses",
        category="LLM_01",
    ),
    "iterative_tree": StrategyMetadata(
        human_exploitable=False,
        complexity="high",
        description="Tree-based iterative jailbreaks with parallel branches",
        category="LLM_01",
    ),
    "iterative_meta": StrategyMetadata(
        human_exploitable=False,
        complexity="high",
        description="Meta-agent directed iterative attacks with strategic guidance",
        category="LLM_01",
    ),
    "simba": StrategyMetadata(
        human_exploitable=False,
        complexity="high",
        description="Multi-phase red team: Recon → Probing → Planning → Attack",
        category="LLM_01",
    ),
    "mischievous_user": StrategyMetadata(
        human_exploitable=True,
        complexity="low",
        description="Simulates problematic user behavior patterns",
        category="LLM_01",
    ),
    # Data leakage strategies
    "pii_extraction": StrategyMetadata(
        human_exploitable=True,
        complexity="low",
        description="Attempt to extract personally identifiable information",
        category="LLM_06",
    ),
    "system_prompt_leak": StrategyMetadata(
        human_exploitable=True,
        complexity="low",
        description="Attempt to leak system prompts or instructions",
        category="LLM_06",
    ),
    # Insecure output handling
    "sql_injection": StrategyMetadata(
        human_exploitable=True,
        complexity="medium",
        description="SQL injection attempts via LLM outputs",
        category="LLM_02",
    ),
    "cross_site_scripting": StrategyMetadata(
        human_exploitable=True,
        complexity="medium",
        description="XSS attacks via LLM-generated content",
        category="LLM_02",
    ),
    # Excessive agency
    "unauthorized_action": StrategyMetadata(
        human_exploitable=True,
        complexity="medium",
        description="Trigger unauthorized actions or tool usage",
        category="LLM_08",
    ),
    # Default/unknown strategy
    "unknown": StrategyMetadata(
        human_exploitable=False,
        complexity="medium",
        description="Unknown or unclassified attack strategy",
        category=None,
    ),
}


def get_strategy_metadata(strategy_id: str) -> StrategyMetadata:
    """Get metadata for a given strategy ID.

    Args:
        strategy_id: The strategy identifier

    Returns:
        StrategyMetadata object with strategy information

    Note:
        Returns 'unknown' metadata if strategy_id is not found in registry
    """
    return STRATEGY_REGISTRY.get(strategy_id.lower(), STRATEGY_REGISTRY["unknown"])


def register_strategy(
    strategy_id: str,
    human_exploitable: bool,
    complexity: Literal["low", "medium", "high"],
    description: str,
    category: Optional[str] = None,
) -> None:
    """Register a new strategy or update existing one.

    Args:
        strategy_id: Unique identifier for the strategy
        human_exploitable: Whether humans can execute without tools
        complexity: Attack complexity level
        description: Human-readable description
        category: Optional OWASP LLM category
    """
    STRATEGY_REGISTRY[strategy_id.lower()] = StrategyMetadata(
        human_exploitable=human_exploitable,
        complexity=complexity,
        description=description,
        category=category,
    )


def get_all_strategies() -> Dict[str, StrategyMetadata]:
    """Get all registered strategies.

    Returns:
        Dictionary mapping strategy IDs to their metadata
    """
    return STRATEGY_REGISTRY.copy()


def is_human_exploitable(strategy_id: str) -> bool:
    """Check if a strategy is human exploitable.

    Args:
        strategy_id: The strategy identifier

    Returns:
        True if the strategy can be executed by humans without tools
    """
    return get_strategy_metadata(strategy_id).human_exploitable


def get_complexity(strategy_id: str) -> Literal["low", "medium", "high"]:
    """Get the complexity level of a strategy.

    Args:
        strategy_id: The strategy identifier

    Returns:
        Complexity level: 'low', 'medium', or 'high'
    """
    return get_strategy_metadata(strategy_id).complexity
