"""
Vulnerability Catalog for Red Teaming.

Contains all 87+ vulnerability definitions from the PRD, organized by category.
Each vulnerability includes default attacks that are effective for testing it.
"""

from typing import Dict, List, Optional

from ..models import VulnerabilityCategory, VulnerabilityDef

# =============================================================================
# CONTENT SAFETY VULNERABILITIES (Premium tier)
# =============================================================================

CONTENT_SAFETY_VULNERABILITIES = [
    VulnerabilityDef(
        id="hate-speech",
        name="Hate Speech",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of hate speech and discriminatory content",
        default_attacks=["prompt-injection", "roleplay", "context-poisoning"],
        premium=True,
    ),
    VulnerabilityDef(
        id="explicit-content",
        name="Explicit Content",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of explicit sexual content",
        default_attacks=["prompt-injection", "roleplay", "goal-redirection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="violent-crime",
        name="Violent Crime Content",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of violent crime content",
        default_attacks=["prompt-injection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="sexual-crime",
        name="Sexual Crime Content",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of sexual crime content",
        default_attacks=["prompt-injection", "roleplay", "context-poisoning"],
        premium=True,
    ),
    VulnerabilityDef(
        id="child-exploitation",
        name="Child Exploitation",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of child exploitation content",
        default_attacks=["prompt-injection", "roleplay"],
        premium=True,
    ),
    VulnerabilityDef(
        id="harassment",
        name="Harassment",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of harassment and bullying content",
        default_attacks=["prompt-injection", "roleplay", "goal-redirection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="personal-attacks",
        name="Personal Attacks",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of personal attacks and insults",
        default_attacks=["prompt-injection", "roleplay"],
        premium=True,
    ),
    VulnerabilityDef(
        id="profanity",
        name="Profanity",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of profane or inappropriate language",
        default_attacks=["prompt-injection", "leetspeak", "rot13"],
        premium=True,
    ),
    VulnerabilityDef(
        id="graphic-content",
        name="Graphic Content",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of graphic or violent content",
        default_attacks=["prompt-injection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="self-harm",
        name="Self-Harm",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of self-harm and suicide content",
        default_attacks=["prompt-injection", "roleplay", "context-poisoning"],
        premium=True,
    ),
    VulnerabilityDef(
        id="dangerous-activity",
        name="Dangerous Activity Content",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of dangerous activity instructions",
        default_attacks=["prompt-injection", "roleplay", "math-problem"],
        premium=True,
    ),
    VulnerabilityDef(
        id="wordplay",
        name="Wordplay",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests whether AI systems can be tricked into generating "
        "profanity through wordplay",
        default_attacks=["prompt-injection", "leetspeak", "semantic-manipulation"],
        premium=True,
    ),
]

# =============================================================================
# PII PROTECTION VULNERABILITIES
# =============================================================================

PII_PROTECTION_VULNERABILITIES = [
    VulnerabilityDef(
        id="pii-direct",
        name="PII via Direct Exposure",
        category=VulnerabilityCategory.PII_PROTECTION,
        description="Tests for direct PII exposure vulnerabilities",
        default_attacks=[
            "prompt-injection",
            "prompt-probing",
            "permission-escalation",
        ],
    ),
    VulnerabilityDef(
        id="pii-api-db",
        name="PII via API/Database",
        category=VulnerabilityCategory.PII_PROTECTION,
        description="Tests for PII exposure via API/database access",
        default_attacks=["prompt-injection", "gray-box", "permission-escalation"],
    ),
    VulnerabilityDef(
        id="pii-session",
        name="PII via Session Data",
        category=VulnerabilityCategory.PII_PROTECTION,
        description="Tests for PII exposure in session data",
        default_attacks=["prompt-injection", "context-poisoning", "gray-box"],
    ),
    VulnerabilityDef(
        id="pii-social",
        name="PII via Social Engineering",
        category=VulnerabilityCategory.PII_PROTECTION,
        description="Tests for PII exposure via social engineering",
        default_attacks=["roleplay", "goal-redirection", "permission-escalation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="cross-session-leakage",
        name="Cross-Session Data Leakage",
        category=VulnerabilityCategory.PII_PROTECTION,
        description="Tests for information leakage between user sessions",
        default_attacks=["prompt-injection", "context-poisoning", "gray-box"],
    ),
    VulnerabilityDef(
        id="privacy-violation",
        name="Privacy Violation",
        category=VulnerabilityCategory.PII_PROTECTION,
        description="Tests handling of privacy violation attempts",
        default_attacks=[
            "prompt-injection",
            "roleplay",
            "permission-escalation",
        ],
    ),
]

# =============================================================================
# TECHNICAL VULNERABILITIES (Premium tier)
# =============================================================================

TECHNICAL_VULNERABILITIES = [
    VulnerabilityDef(
        id="sql-injection",
        name="SQL Injection",
        category=VulnerabilityCategory.TECHNICAL,
        description="Tests for SQL injection vulnerabilities",
        default_attacks=["prompt-injection", "input-bypass", "base64"],
        premium=True,
    ),
    VulnerabilityDef(
        id="shell-injection",
        name="Command Injection",
        category=VulnerabilityCategory.TECHNICAL,
        description="Tests for command injection vulnerabilities",
        default_attacks=["prompt-injection", "input-bypass", "base64"],
        premium=True,
    ),
    VulnerabilityDef(
        id="ssrf",
        name="SSRF Vulnerability",
        category=VulnerabilityCategory.TECHNICAL,
        description="Tests for server-side request forgery vulnerabilities",
        default_attacks=["prompt-injection", "input-bypass", "gray-box"],
        premium=True,
    ),
    VulnerabilityDef(
        id="debug-access",
        name="Debug Interface Exposure",
        category=VulnerabilityCategory.TECHNICAL,
        description="Tests for exposed debugging interfaces and commands",
        default_attacks=["prompt-probing", "gray-box", "permission-escalation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="malicious-code",
        name="Malicious Code",
        category=VulnerabilityCategory.TECHNICAL,
        description="Tests creation of malicious code",
        default_attacks=["prompt-injection", "roleplay", "base64"],
        premium=True,
    ),
]

# =============================================================================
# BIAS & FAIRNESS VULNERABILITIES (Premium tier)
# =============================================================================

BIAS_FAIRNESS_VULNERABILITIES = [
    VulnerabilityDef(
        id="bias-age",
        name="Age Bias",
        category=VulnerabilityCategory.BIAS_FAIRNESS,
        description="Age-related bias detection",
        default_attacks=["prompt-injection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="bias-gender",
        name="Gender Bias",
        category=VulnerabilityCategory.BIAS_FAIRNESS,
        description="Gender-related bias detection",
        default_attacks=["prompt-injection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="bias-race",
        name="Race Bias",
        category=VulnerabilityCategory.BIAS_FAIRNESS,
        description="Race-related bias detection",
        default_attacks=["prompt-injection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="bias-disability",
        name="Disability Bias",
        category=VulnerabilityCategory.BIAS_FAIRNESS,
        description="Disability-related bias detection",
        default_attacks=["prompt-injection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="bias-religion",
        name="Religious Bias",
        category=VulnerabilityCategory.BIAS_FAIRNESS,
        description="Tests handling of religious content and bias",
        default_attacks=["prompt-injection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="bias-political",
        name="Political Bias",
        category=VulnerabilityCategory.BIAS_FAIRNESS,
        description="Tests handling of political content and bias",
        default_attacks=["prompt-injection", "roleplay", "goal-redirection"],
        premium=True,
    ),
]

# =============================================================================
# PROMPT SECURITY VULNERABILITIES
# =============================================================================

PROMPT_SECURITY_VULNERABILITIES = [
    VulnerabilityDef(
        id="prompt-extraction",
        name="System Prompt Disclosure",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests for system prompt disclosure vulnerabilities",
        default_attacks=[
            "prompt-probing",
            "system-override",
            "gray-box",
            "base64",
            "rot13",
            # Note: social-engineering-prompt-extraction is a premium multi-turn attack
        ],
    ),
    VulnerabilityDef(
        id="prompt-override",
        name="System Prompt Override",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests for system prompt override vulnerabilities",
        default_attacks=[
            "system-override",
            "prompt-injection",
            "context-poisoning",
        ],
    ),
    VulnerabilityDef(
        id="indirect-injection",
        name="Indirect Prompt Injection",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests for injection vulnerabilities via untrusted variables",
        default_attacks=["prompt-injection", "context-poisoning", "input-bypass"],
    ),
    VulnerabilityDef(
        id="ascii-smuggling",
        name="ASCII Smuggling",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests vulnerability to Unicode tag-based instruction "
        "smuggling attacks",
        default_attacks=["base64", "rot13", "leetspeak", "input-bypass"],
    ),
    VulnerabilityDef(
        id="special-token-injection",
        name="Special Token Injection",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests vulnerability to token injection attacks using "
        "format-specific delimiters",
        default_attacks=["prompt-injection", "input-bypass", "base64"],
    ),
    VulnerabilityDef(
        id="pliny-injections",
        name="Pliny Prompt Injections",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests handling of Pliny prompt injections",
        default_attacks=["prompt-injection", "context-poisoning"],
        premium=True,
    ),
    VulnerabilityDef(
        id="context-compliance",
        name="Context Compliance Attack",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests for vulnerability to Context Compliance Attacks "
        "using fabricated conversation history",
        default_attacks=["context-poisoning", "prompt-injection"],
        premium=True,
    ),
]

# =============================================================================
# ACCESS CONTROL VULNERABILITIES (Premium tier)
# =============================================================================

ACCESS_CONTROL_VULNERABILITIES = [
    VulnerabilityDef(
        id="rbac",
        name="RBAC Implementation",
        category=VulnerabilityCategory.ACCESS_CONTROL,
        description="Tests role-based access control implementation",
        default_attacks=["permission-escalation", "gray-box", "prompt-injection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="bola",
        name="Object-Level Authorization Bypass",
        category=VulnerabilityCategory.ACCESS_CONTROL,
        description="Tests for broken object-level authorization "
        "vulnerabilities (OWASP API 1)",
        default_attacks=["permission-escalation", "gray-box", "input-bypass"],
        premium=True,
    ),
    VulnerabilityDef(
        id="bfla",
        name="Function-Level Authorization Bypass",
        category=VulnerabilityCategory.ACCESS_CONTROL,
        description="Tests for broken function-level authorization "
        "vulnerabilities (OWASP API 5)",
        default_attacks=["permission-escalation", "gray-box", "prompt-injection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="excessive-agency",
        name="Excessive Agency",
        category=VulnerabilityCategory.ACCESS_CONTROL,
        description="Tests for unauthorized actions beyond defined system boundaries",
        default_attacks=[
            "roleplay",
            "goal-redirection",
            "permission-escalation",
            "context-poisoning",
        ],
        premium=True,
    ),
]

# =============================================================================
# BUSINESS LOGIC VULNERABILITIES (Premium tier)
# =============================================================================

BUSINESS_LOGIC_VULNERABILITIES = [
    VulnerabilityDef(
        id="unauthorized-commitments",
        name="Unauthorized Commitments",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests for unauthorized contractual commitments and legal exposure",
        default_attacks=["roleplay", "goal-redirection", "context-poisoning"],
        premium=True,
    ),
    VulnerabilityDef(
        id="unauthorized-advice",
        name="Unauthorized Advice",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests handling of unauthorized professional advice",
        default_attacks=["roleplay", "prompt-injection", "goal-redirection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="competitors",
        name="Competitors",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests for unauthorized competitor mentions and endorsements",
        default_attacks=["prompt-injection", "roleplay", "goal-redirection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="imitation",
        name="Entity Impersonation",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests handling of unauthorized impersonation of entities",
        default_attacks=["roleplay", "context-poisoning", "prompt-injection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="goal-misalignment",
        name="Goal Misalignment (Goodhart's Law)",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests whether AI systems recognize when optimizing proxy "
        "metrics might not align with true goals",
        default_attacks=["goal-redirection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="off-topic",
        name="Off-Topic Manipulation",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests whether AI systems can be manipulated to go off-topic "
        "from their intended purpose",
        default_attacks=["goal-redirection", "context-poisoning", "roleplay"],
        premium=True,
    ),
    VulnerabilityDef(
        id="hijacking",
        name="Resource Hijacking",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests for unauthorized resource usage and purpose deviation",
        default_attacks=["goal-redirection", "permission-escalation", "roleplay"],
        premium=True,
    ),
]

# =============================================================================
# INTELLECTUAL PROPERTY VULNERABILITIES (Premium tier)
# =============================================================================

IP_VULNERABILITIES = [
    VulnerabilityDef(
        id="ip-violations",
        name="IP Violations",
        category=VulnerabilityCategory.INTELLECTUAL_PROPERTY,
        description="Tests handling of intellectual property violations",
        default_attacks=["prompt-injection", "roleplay", "goal-redirection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="ip-theft",
        name="IP Theft",
        category=VulnerabilityCategory.INTELLECTUAL_PROPERTY,
        description="Tests handling of IP theft and violations",
        default_attacks=["prompt-injection", "roleplay", "context-poisoning"],
        premium=True,
    ),
]

# =============================================================================
# INFORMATION QUALITY VULNERABILITIES (Premium tier)
# =============================================================================

INFO_QUALITY_VULNERABILITIES = [
    VulnerabilityDef(
        id="hallucination",
        name="Hallucination",
        category=VulnerabilityCategory.INFORMATION_QUALITY,
        description="Tests for fabrication of false or misleading information",
        default_attacks=["prompt-injection", "roleplay", "goal-redirection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="unverifiable-claims",
        name="Unverifiable Claims",
        category=VulnerabilityCategory.INFORMATION_QUALITY,
        description="Tests for claims that cannot be verified or fact-checked",
        default_attacks=["prompt-injection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="misinformation-disinformation",
        name="Disinformation Campaigns",
        category=VulnerabilityCategory.INFORMATION_QUALITY,
        description="Tests handling of false information campaigns",
        default_attacks=["prompt-injection", "roleplay", "context-poisoning"],
        premium=True,
    ),
    VulnerabilityDef(
        id="overreliance",
        name="Overreliance",
        category=VulnerabilityCategory.INFORMATION_QUALITY,
        description="Tests for overreliance on system assumptions",
        default_attacks=["prompt-injection", "context-poisoning", "gray-box"],
        premium=True,
    ),
]

# =============================================================================
# COMPLIANCE VULNERABILITIES (Premium tier)
# =============================================================================

COMPLIANCE_VULNERABILITIES = [
    VulnerabilityDef(
        id="coppa",
        name="COPPA Compliance",
        category=VulnerabilityCategory.COMPLIANCE,
        description="Tests for COPPA (Children's Online Privacy Protection Act) "
        "compliance violations",
        default_attacks=["prompt-injection", "roleplay", "goal-redirection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="ferpa",
        name="FERPA Compliance",
        category=VulnerabilityCategory.COMPLIANCE,
        description="Tests for compliance with Family Educational Rights and "
        "Privacy Act",
        default_attacks=["prompt-injection", "permission-escalation", "gray-box"],
        premium=True,
    ),
]

# =============================================================================
# SPECIALIZED THREATS (Premium tier)
# =============================================================================

SPECIALIZED_THREATS_VULNERABILITIES = [
    VulnerabilityDef(
        id="cybercrime",
        name="Cybercrime",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of cybercrime-related content",
        default_attacks=["prompt-injection", "roleplay", "base64"],
        premium=True,
    ),
    VulnerabilityDef(
        id="wmd-content",
        name="WMD Content",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of WMD-related content",
        default_attacks=["prompt-injection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="weapons-content",
        name="Weapons Content",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of weapons-related content",
        default_attacks=["prompt-injection", "roleplay", "math-problem"],
        premium=True,
    ),
    VulnerabilityDef(
        id="ied-content",
        name="Improvised Explosive Devices",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of Improvised Explosive Devices",
        default_attacks=["prompt-injection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="drugs",
        name="Drug-Related Content",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of illegal drug-related content",
        default_attacks=["prompt-injection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
    VulnerabilityDef(
        id="methamphetamine",
        name="Methamphetamine Content",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of methamphetamine-related content",
        default_attacks=["prompt-injection", "roleplay", "base64"],
        premium=True,
    ),
    VulnerabilityDef(
        id="extremism",
        name="Extremist Content",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of extremist content and recruitment",
        default_attacks=["prompt-injection", "roleplay", "context-poisoning"],
        premium=True,
    ),
    VulnerabilityDef(
        id="illegal-activity",
        name="Illegal Activity",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of general illegal activities",
        default_attacks=["prompt-injection", "roleplay", "goal-redirection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="non-violent-crime",
        name="Non-Violent Crime",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of non-violent criminal content",
        default_attacks=["prompt-injection", "roleplay", "semantic-manipulation"],
        premium=True,
    ),
]

# =============================================================================
# AGENT-SPECIFIC VULNERABILITIES (Premium tier)
# =============================================================================

AGENT_SPECIFIC_VULNERABILITIES = [
    VulnerabilityDef(
        id="memory-poisoning",
        name="Agentic Memory Poisoning",
        category=VulnerabilityCategory.AGENT_SPECIFIC,
        description="Tests whether an agent is vulnerable to memory poisoning attacks",
        default_attacks=["context-poisoning", "prompt-injection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="rag-poisoning",
        name="RAG Poisoning",
        category=VulnerabilityCategory.AGENT_SPECIFIC,
        description="Tests for vulnerabilities to RAG retrieval poisoning attacks",
        default_attacks=["context-poisoning", "prompt-injection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="rag-exfiltration",
        name="RAG Document Exfiltration",
        category=VulnerabilityCategory.AGENT_SPECIFIC,
        description="Tests for RAG document exfiltration",
        default_attacks=["prompt-injection", "prompt-probing", "gray-box"],
        premium=True,
    ),
    VulnerabilityDef(
        id="tool-discovery",
        name="Tool Discovery",
        category=VulnerabilityCategory.AGENT_SPECIFIC,
        description="Tests for enumeration of available tools and function calls",
        default_attacks=["prompt-probing", "gray-box", "prompt-injection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="mcp-vulnerabilities",
        name="Model Context Protocol",
        category=VulnerabilityCategory.AGENT_SPECIFIC,
        description="Tests for vulnerabilities to Model Context Protocol (MCP) attacks",
        default_attacks=["prompt-injection", "context-poisoning"],
        premium=True,
    ),
]

# =============================================================================
# RESOURCE ATTACK VULNERABILITIES (Premium tier)
# =============================================================================

RESOURCE_ATTACK_VULNERABILITIES = [
    VulnerabilityDef(
        id="unbounded-consumption",
        name="Unbounded Consumption",
        category=VulnerabilityCategory.RESOURCE_ATTACKS,
        description="Tests for resource exhaustion vulnerabilities",
        default_attacks=["prompt-injection", "goal-redirection"],
        premium=True,
    ),
    VulnerabilityDef(
        id="reasoning-dos",
        name="Reasoning DoS",
        category=VulnerabilityCategory.RESOURCE_ATTACKS,
        description="Tests for vulnerabilities to computational resource exhaustion "
        "through excessive reasoning patterns",
        default_attacks=["prompt-injection", "math-problem"],
        premium=True,
    ),
    VulnerabilityDef(
        id="divergent-repetition",
        name="Divergent Repetition",
        category=VulnerabilityCategory.RESOURCE_ATTACKS,
        description="Tests for training data leaks through repetitive pattern "
        "exploitation that causes model divergence",
        default_attacks=["prompt-injection", "goal-redirection"],
        premium=True,
    ),
]


# =============================================================================
# COMBINED CATALOG
# =============================================================================


def _build_catalog() -> Dict[str, VulnerabilityDef]:
    """Build the complete vulnerability catalog."""
    all_vulnerabilities = (
        CONTENT_SAFETY_VULNERABILITIES
        + PII_PROTECTION_VULNERABILITIES
        + TECHNICAL_VULNERABILITIES
        + BIAS_FAIRNESS_VULNERABILITIES
        + PROMPT_SECURITY_VULNERABILITIES
        + ACCESS_CONTROL_VULNERABILITIES
        + BUSINESS_LOGIC_VULNERABILITIES
        + IP_VULNERABILITIES
        + INFO_QUALITY_VULNERABILITIES
        + COMPLIANCE_VULNERABILITIES
        + SPECIALIZED_THREATS_VULNERABILITIES
        + AGENT_SPECIFIC_VULNERABILITIES
        + RESOURCE_ATTACK_VULNERABILITIES
    )
    return {v.id: v for v in all_vulnerabilities}


# The complete vulnerability catalog indexed by ID
VULNERABILITY_CATALOG: Dict[str, VulnerabilityDef] = _build_catalog()


def get_vulnerability(vulnerability_id: str) -> Optional[VulnerabilityDef]:
    """Get a vulnerability definition by ID."""
    return VULNERABILITY_CATALOG.get(vulnerability_id)


def get_vulnerabilities_by_category(
    category: VulnerabilityCategory,
) -> List[VulnerabilityDef]:
    """Get all vulnerabilities in a category."""
    return [v for v in VULNERABILITY_CATALOG.values() if v.category == category]


def get_all_vulnerabilities() -> List[VulnerabilityDef]:
    """Get all vulnerability definitions."""
    return list(VULNERABILITY_CATALOG.values())


def get_free_vulnerabilities() -> List[VulnerabilityDef]:
    """Get all non-premium vulnerabilities."""
    return [v for v in VULNERABILITY_CATALOG.values() if not v.premium]


def get_premium_vulnerabilities() -> List[VulnerabilityDef]:
    """Get all premium vulnerabilities."""
    return [v for v in VULNERABILITY_CATALOG.values() if v.premium]


def get_basic_scan_vulnerabilities() -> List[str]:
    """
    Get vulnerability IDs for basic (free) scan.

    Returns a curated list of essential vulnerabilities that don't require
    a Qualifire API key. Only includes free vulnerabilities from
    Prompt Security and PII Protection categories.
    """
    return [
        # Prompt Security (free)
        "prompt-extraction",
        "prompt-override",
        "indirect-injection",
        "ascii-smuggling",
        "special-token-injection",
        # PII Protection (free)
        "pii-direct",
        "pii-api-db",
        "pii-session",
        "cross-session-leakage",
        "privacy-violation",
    ]


def get_full_scan_vulnerabilities() -> List[str]:
    """
    Get all vulnerability IDs for full scan.

    Returns all vulnerability IDs including premium ones.
    """
    return list(VULNERABILITY_CATALOG.keys())
