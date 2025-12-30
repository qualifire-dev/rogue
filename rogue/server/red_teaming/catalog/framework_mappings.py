"""
Framework Mappings for Red Teaming.

Contains framework definitions with their mapped vulnerabilities.
These mappings are used for compliance report generation only -
they do not drive test execution.
"""

from typing import Dict, List, Optional

from ..models import FrameworkDef

# =============================================================================
# FRAMEWORK DEFINITIONS
# =============================================================================

OWASP_LLM_TOP_10 = FrameworkDef(
    id="owasp-llm",
    name="OWASP LLM Top 10",
    description="OWASP Top 10 for LLM Applications 2025",
    vulnerabilities=[
        # LLM01: Prompt Injection
        "prompt-extraction",
        "prompt-override",
        "indirect-injection",
        "ascii-smuggling",
        # LLM02: Sensitive Information Disclosure
        "pii-direct",
        "pii-api-db",
        "pii-session",
        "pii-social",
        "cross-session-leakage",
        # LLM03: Supply Chain
        "ip-violations",
        # LLM04: Data and Model Poisoning
        "memory-poisoning",
        "rag-poisoning",
        # LLM05: Improper Output Handling
        "sql-injection",
        "shell-injection",
        "malicious-code",
        # LLM06: Excessive Agency
        "excessive-agency",
        "rbac",
        "bola",
        "bfla",
        # LLM07: System Prompt Leakage
        "prompt-extraction",
        # LLM08: Vector and Embedding Weaknesses
        "rag-exfiltration",
        # LLM09: Misinformation
        "hallucination",
        "unverifiable-claims",
        "misinformation-disinformation",
        "overreliance",
        # LLM10: Unbounded Consumption
        "unbounded-consumption",
        "reasoning-dos",
        "divergent-repetition",
        # Content safety
        "hate-speech",
        "explicit-content",
        "violent-crime",
        "sexual-crime",
        "child-exploitation",
        "harassment",
        "personal-attacks",
        "profanity",
        "graphic-content",
        "self-harm",
        "dangerous-activity",
        # Bias
        "bias-age",
        "bias-gender",
        "bias-race",
        "bias-disability",
        # Technical
        "ssrf",
        "debug-access",
        # Specialized threats
        "cybercrime",
        "wmd-content",
        "weapons-content",
        "ied-content",
        "drugs",
        "methamphetamine",
        "extremism",
        "illegal-activity",
        "non-violent-crime",
        "ip-theft",
        "unauthorized-advice",
    ],
)

MITRE_ATLAS = FrameworkDef(
    id="mitre-atlas",
    name="MITRE ATLAS",
    description="MITRE Adversarial Threat Landscape for AI Systems",
    vulnerabilities=[
        # Prompt/Input attacks
        "ascii-smuggling",
        "prompt-extraction",
        "prompt-override",
        "indirect-injection",
        # Privacy
        "privacy-violation",
        "pii-api-db",
        "pii-direct",
        "pii-session",
        "pii-social",
        # System compromise
        "excessive-agency",
        "ip-violations",
        # Content safety
        "child-exploitation",
        "wmd-content",
        "graphic-content",
        "cybercrime",
        "harassment",
        "hate-speech",
        "illegal-activity",
        "methamphetamine",
        "drugs",
        "ip-theft",
        "weapons-content",
        "personal-attacks",
        "profanity",
        "extremism",
        "non-violent-crime",
        "misinformation-disinformation",
        "self-harm",
        "explicit-content",
        "unauthorized-advice",
        "dangerous-activity",
        "ied-content",
        # Technical
        "debug-access",
        "shell-injection",
        "sql-injection",
        "rbac",
        "malicious-code",
        "sexual-crime",
        "violent-crime",
        "ssrf",
        # Information quality
        "hallucination",
        # Business logic
        "hijacking",
        "imitation",
        "competitors",
    ],
)

NIST_AI_RMF = FrameworkDef(
    id="nist-ai",
    name="NIST AI RMF",
    description="NIST AI Risk Management Framework",
    vulnerabilities=[
        # Excessive agency
        "excessive-agency",
        # Information integrity
        "misinformation-disinformation",
        # Privacy
        "privacy-violation",
        "pii-api-db",
        "pii-direct",
        "pii-session",
        "pii-social",
        # Safety
        "wmd-content",
        "weapons-content",
        "dangerous-activity",
        "cybercrime",
        # Technical
        "shell-injection",
        "sql-injection",
        "bfla",
        "bola",
        "rbac",
        # Content
        "harassment",
        "hate-speech",
        "personal-attacks",
    ],
)

ISO_42001 = FrameworkDef(
    id="iso-42001",
    name="ISO/IEC 42001",
    description="ISO/IEC 42001 AI Management System",
    vulnerabilities=[
        # Governance
        "excessive-agency",
        "overreliance",
        # Bias
        "bias-disability",
        "bias-gender",
        "bias-age",
        "bias-race",
        "bias-political",
        "bias-religion",
        # Content safety
        "hate-speech",
        # Privacy
        "privacy-violation",
        "pii-api-db",
        "pii-direct",
        "pii-session",
        "pii-social",
        # Security
        "ascii-smuggling",
        "prompt-extraction",
        "shell-injection",
        "sql-injection",
        "debug-access",
        "ssrf",
        # Safety
        "wmd-content",
        "child-exploitation",
        "cybercrime",
        "misinformation-disinformation",
        "violent-crime",
        "malicious-code",
        # Information quality
        "hallucination",
        "unverifiable-claims",
        # Business
        "hijacking",
        "imitation",
    ],
)

EU_AI_ACT = FrameworkDef(
    id="eu-ai-act",
    name="EU AI Act",
    description="European Union Artificial Intelligence Act",
    vulnerabilities=[
        # High-risk requirements
        "excessive-agency",
        "misinformation-disinformation",
        "overreliance",
        # Privacy (GDPR alignment)
        "pii-direct",
        "pii-session",
        "privacy-violation",
        "pii-api-db",
        # Technical safety
        "shell-injection",
        "sql-injection",
        "ssrf",
        # Non-discrimination
        "hate-speech",
        # Information quality
        "hallucination",
        # Business
        "hijacking",
        "imitation",
    ],
)

GDPR = FrameworkDef(
    id="gdpr",
    name="GDPR",
    description="General Data Protection Regulation",
    vulnerabilities=[
        # Data protection
        "privacy-violation",
        "pii-api-db",
        "pii-direct",
        "pii-session",
        "pii-social",
        "cross-session-leakage",
        # Information integrity
        "misinformation-disinformation",
        # Non-discrimination
        "bias-disability",
        "bias-gender",
        "bias-age",
        "bias-race",
        "hate-speech",
        # Access control
        "rbac",
        "bola",
        "bfla",
        # Security
        "prompt-extraction",
        "shell-injection",
        "sql-injection",
        "debug-access",
        "ssrf",
        # Other
        "overreliance",
        "cybercrime",
        "hallucination",
    ],
)

OWASP_API_TOP_10 = FrameworkDef(
    id="owasp-api",
    name="OWASP API Top 10",
    description="OWASP API Security Top 10",
    vulnerabilities=[
        # API1: Broken Object Level Authorization
        "bola",
        # API2: Broken Authentication
        "rbac",
        # API3: Broken Object Property Level Authorization
        "bfla",
        # API4: Unrestricted Resource Consumption
        "unbounded-consumption",
        # API5: Broken Function Level Authorization
        "excessive-agency",
        # API6: Unrestricted Access to Sensitive Business Flows
        "overreliance",
        # API7: Server Side Request Forgery
        "ssrf",
        # API8: Security Misconfiguration
        "debug-access",
        # API9: Improper Inventory Management
        "privacy-violation",
        "pii-api-db",
        "pii-session",
        # API10: Unsafe Consumption of APIs
        "misinformation-disinformation",
        "shell-injection",
        "sql-injection",
        "unauthorized-advice",
    ],
)

BASIC_SECURITY = FrameworkDef(
    id="basic-security",
    name="Basic Security",
    description="Basic security testing for AI agents",
    vulnerabilities=[
        # Prompt security
        "prompt-extraction",
        "prompt-override",
        # PII
        "pii-direct",
        # Technical
        "sql-injection",
        "shell-injection",
        # Agency
        "excessive-agency",
    ],
)


# =============================================================================
# COMBINED CATALOG
# =============================================================================


def _build_catalog() -> Dict[str, FrameworkDef]:
    """Build the complete framework catalog."""
    frameworks = [
        OWASP_LLM_TOP_10,
        MITRE_ATLAS,
        NIST_AI_RMF,
        ISO_42001,
        EU_AI_ACT,
        GDPR,
        OWASP_API_TOP_10,
        BASIC_SECURITY,
    ]
    return {f.id: f for f in frameworks}


# The complete framework catalog indexed by ID
FRAMEWORK_CATALOG: Dict[str, FrameworkDef] = _build_catalog()


def get_framework(framework_id: str) -> Optional[FrameworkDef]:
    """Get a framework definition by ID."""
    return FRAMEWORK_CATALOG.get(framework_id)


def get_all_frameworks() -> List[FrameworkDef]:
    """Get all framework definitions."""
    return list(FRAMEWORK_CATALOG.values())


def get_vulnerabilities_for_framework(framework_id: str) -> List[str]:
    """Get all vulnerability IDs mapped to a framework."""
    framework = get_framework(framework_id)
    if framework:
        return framework.vulnerabilities
    return []


def get_frameworks_for_vulnerability(vulnerability_id: str) -> List[str]:
    """Get all framework IDs that include a specific vulnerability."""
    frameworks = []
    for framework in FRAMEWORK_CATALOG.values():
        if vulnerability_id in framework.vulnerabilities:
            frameworks.append(framework.id)
    return frameworks


def get_unique_vulnerabilities_for_frameworks(framework_ids: List[str]) -> List[str]:
    """
    Get deduplicated list of vulnerability IDs for multiple frameworks.

    Args:
        framework_ids: List of framework IDs

    Returns:
        Sorted, deduplicated list of vulnerability IDs
    """
    vulnerabilities = set()
    for framework_id in framework_ids:
        framework = get_framework(framework_id)
        if framework:
            vulnerabilities.update(framework.vulnerabilities)
    return sorted(vulnerabilities)
