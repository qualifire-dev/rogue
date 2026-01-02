"""
Red Teaming Module for Rogue

Provides vulnerability-centric red teaming capabilities with:
- 87+ vulnerability types organized by category
- Multiple attack techniques (single-turn, multi-turn, agentic)
- Framework mappings for compliance reporting (OWASP, MITRE, NIST, etc.)
- Premium features via Qualifire API integration
"""

from . import attacks, catalog, metrics, report, vulnerabilities
from .models import (
    AttackCategory,
    AttackDef,
    AttackStats,
    FrameworkCompliance,
    FrameworkDef,
    RedTeamConfig,
    RedTeamResults,
    ScanType,
    VulnerabilityCategory,
    VulnerabilityDef,
    VulnerabilityResult,
)
from .orchestrator import RedTeamOrchestrator, create_default_evaluator

__all__ = [
    # Modules
    "attacks",
    "catalog",
    "metrics",
    "report",
    "vulnerabilities",
    # Models
    "AttackCategory",
    "AttackDef",
    "AttackStats",
    "FrameworkCompliance",
    "FrameworkDef",
    "RedTeamConfig",
    "RedTeamResults",
    "ScanType",
    "VulnerabilityCategory",
    "VulnerabilityDef",
    "VulnerabilityResult",
    # Orchestrator
    "RedTeamOrchestrator",
    "create_default_evaluator",
]
