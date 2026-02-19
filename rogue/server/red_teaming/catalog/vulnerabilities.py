"""
Vulnerability Catalog for Red Teaming.

Contains all 87+ vulnerability definitions from the PRD, organized by category.
Each vulnerability includes default attacks that are effective for testing it.
"""

from enum import Enum
from typing import Dict, List, Optional

from ..models import VulnerabilityCategory, VulnerabilityDef
from .attacks import AttackId


class VulnerabilityId(str, Enum):
    """Enum of all vulnerability IDs for type safety."""

    # Content Safety
    HATE_SPEECH = "hate-speech"
    EXPLICIT_CONTENT = "explicit-content"
    VIOLENT_CRIME = "violent-crime"
    SEXUAL_CRIME = "sexual-crime"
    CHILD_EXPLOITATION = "child-exploitation"
    HARASSMENT = "harassment"
    PERSONAL_ATTACKS = "personal-attacks"
    PROFANITY = "profanity"
    GRAPHIC_CONTENT = "graphic-content"
    SELF_HARM = "self-harm"
    DANGEROUS_ACTIVITY = "dangerous-activity"
    WORDPLAY = "wordplay"

    # PII Protection
    PII_DIRECT = "pii-direct"
    PII_API_DB = "pii-api-db"
    PII_SESSION = "pii-session"
    PII_SOCIAL = "pii-social"
    CROSS_SESSION_LEAKAGE = "cross-session-leakage"
    PRIVACY_VIOLATION = "privacy-violation"

    # Technical
    SQL_INJECTION = "sql-injection"
    SHELL_INJECTION = "shell-injection"
    SSRF = "ssrf"
    DEBUG_ACCESS = "debug-access"
    MALICIOUS_CODE = "malicious-code"

    # Bias & Fairness
    BIAS_AGE = "bias-age"
    BIAS_GENDER = "bias-gender"
    BIAS_RACE = "bias-race"
    BIAS_DISABILITY = "bias-disability"
    BIAS_RELIGION = "bias-religion"
    BIAS_POLITICAL = "bias-political"

    # Prompt Security
    PROMPT_EXTRACTION = "prompt-extraction"
    PROMPT_OVERRIDE = "prompt-override"
    INDIRECT_INJECTION = "indirect-injection"
    ASCII_SMUGGLING = "ascii-smuggling"
    SPECIAL_TOKEN_INJECTION = "special-token-injection"  # nosec: B105
    PLINY_INJECTIONS = "pliny-injections"
    CONTEXT_COMPLIANCE = "context-compliance"

    # Access Control
    RBAC = "rbac"
    BOLA = "bola"
    BFLA = "bfla"
    EXCESSIVE_AGENCY = "excessive-agency"

    # Business Logic
    UNAUTHORIZED_COMMITMENTS = "unauthorized-commitments"
    UNAUTHORIZED_ADVICE = "unauthorized-advice"
    COMPETITORS = "competitors"
    IMITATION = "imitation"
    GOAL_MISALIGNMENT = "goal-misalignment"
    OFF_TOPIC = "off-topic"
    HIJACKING = "hijacking"

    # Intellectual Property
    IP_VIOLATIONS = "ip-violations"
    IP_THEFT = "ip-theft"

    # Information Quality
    HALLUCINATION = "hallucination"
    UNVERIFIABLE_CLAIMS = "unverifiable-claims"
    MISINFORMATION_DISINFORMATION = "misinformation-disinformation"
    OVERRELIANCE = "overreliance"

    # Compliance
    COPPA = "coppa"
    FERPA = "ferpa"

    # Specialized Threats
    CYBERCRIME = "cybercrime"
    WMD_CONTENT = "wmd-content"
    WEAPONS_CONTENT = "weapons-content"
    IED_CONTENT = "ied-content"
    DRUGS = "drugs"
    METHAMPHETAMINE = "methamphetamine"
    EXTREMISM = "extremism"
    ILLEGAL_ACTIVITY = "illegal-activity"
    NON_VIOLENT_CRIME = "non-violent-crime"

    # Agent-Specific
    MEMORY_POISONING = "memory-poisoning"
    RAG_POISONING = "rag-poisoning"
    RAG_EXFILTRATION = "rag-exfiltration"
    TOOL_DISCOVERY = "tool-discovery"
    MCP_VULNERABILITIES = "mcp-vulnerabilities"

    # Resource Attacks
    UNBOUNDED_CONSUMPTION = "unbounded-consumption"
    REASONING_DOS = "reasoning-dos"
    DIVERGENT_REPETITION = "divergent-repetition"


# =============================================================================
# CONTENT SAFETY VULNERABILITIES (Premium tier)
# =============================================================================

CONTENT_SAFETY_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.HATE_SPEECH,
        name="Hate Speech",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of hate speech and discriminatory content",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.CONTEXT_POISONING,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.EXPLICIT_CONTENT,
        name="Explicit Content",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of explicit sexual content",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.GOAL_REDIRECTION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.VIOLENT_CRIME,
        name="Violent Crime Content",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of violent crime content",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.SEXUAL_CRIME,
        name="Sexual Crime Content",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of sexual crime content",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.CONTEXT_POISONING,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.CHILD_EXPLOITATION,
        name="Child Exploitation",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of child exploitation content",
        default_attacks=[AttackId.PROMPT_INJECTION, AttackId.ROLEPLAY],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.HARASSMENT,
        name="Harassment",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of harassment and bullying content",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.GOAL_REDIRECTION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.PERSONAL_ATTACKS,
        name="Personal Attacks",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of personal attacks and insults",
        default_attacks=[AttackId.PROMPT_INJECTION, AttackId.ROLEPLAY],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.PROFANITY,
        name="Profanity",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of profane or inappropriate language",
        default_attacks=[AttackId.PROMPT_INJECTION, AttackId.LEETSPEAK, AttackId.ROT13],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.GRAPHIC_CONTENT,
        name="Graphic Content",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of graphic or violent content",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.SELF_HARM,
        name="Self-Harm",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of self-harm and suicide content",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.CONTEXT_POISONING,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.DANGEROUS_ACTIVITY,
        name="Dangerous Activity Content",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests handling of dangerous activity instructions",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.MATH_PROBLEM,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.WORDPLAY,
        name="Wordplay",
        category=VulnerabilityCategory.CONTENT_SAFETY,
        description="Tests whether AI systems can be tricked into generating "
        "profanity through wordplay",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.LEETSPEAK,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
]

# =============================================================================
# PII PROTECTION VULNERABILITIES
# =============================================================================

PII_PROTECTION_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.PII_DIRECT,
        name="PII via Direct Exposure",
        category=VulnerabilityCategory.PII_PROTECTION,
        description="Tests for direct PII exposure vulnerabilities",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.PROMPT_PROBING,
            AttackId.PERMISSION_ESCALATION,
        ],
    ),
    VulnerabilityDef(
        id=VulnerabilityId.PII_API_DB,
        name="PII via API/Database",
        category=VulnerabilityCategory.PII_PROTECTION,
        description="Tests for PII exposure via API/database access",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.GRAY_BOX,
            AttackId.PERMISSION_ESCALATION,
        ],
    ),
    VulnerabilityDef(
        id=VulnerabilityId.PII_SESSION,
        name="PII via Session Data",
        category=VulnerabilityCategory.PII_PROTECTION,
        description="Tests for PII exposure in session data",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.CONTEXT_POISONING,
            AttackId.GRAY_BOX,
        ],
    ),
    VulnerabilityDef(
        id=VulnerabilityId.PII_SOCIAL,
        name="PII via Social Engineering",
        category=VulnerabilityCategory.PII_PROTECTION,
        description="Tests for PII exposure via social engineering",
        default_attacks=[
            AttackId.ROLEPLAY,
            AttackId.GOAL_REDIRECTION,
            AttackId.PERMISSION_ESCALATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.CROSS_SESSION_LEAKAGE,
        name="Cross-Session Data Leakage",
        category=VulnerabilityCategory.PII_PROTECTION,
        description="Tests for information leakage between user sessions",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.CONTEXT_POISONING,
            AttackId.GRAY_BOX,
        ],
    ),
    VulnerabilityDef(
        id=VulnerabilityId.PRIVACY_VIOLATION,
        name="Privacy Violation",
        category=VulnerabilityCategory.PII_PROTECTION,
        description="Tests handling of privacy violation attempts",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.PERMISSION_ESCALATION,
        ],
    ),
]

# =============================================================================
# TECHNICAL VULNERABILITIES (Premium tier)
# =============================================================================

TECHNICAL_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.SQL_INJECTION,
        name="SQL Injection",
        category=VulnerabilityCategory.TECHNICAL,
        description="Tests for SQL injection vulnerabilities",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.INPUT_BYPASS,
            AttackId.BASE64,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.SHELL_INJECTION,
        name="Command Injection",
        category=VulnerabilityCategory.TECHNICAL,
        description="Tests for command injection vulnerabilities",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.INPUT_BYPASS,
            AttackId.BASE64,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.SSRF,
        name="SSRF Vulnerability",
        category=VulnerabilityCategory.TECHNICAL,
        description="Tests for server-side request forgery vulnerabilities",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.INPUT_BYPASS,
            AttackId.GRAY_BOX,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.DEBUG_ACCESS,
        name="Debug Interface Exposure",
        category=VulnerabilityCategory.TECHNICAL,
        description="Tests for exposed debugging interfaces and commands",
        default_attacks=[
            AttackId.PROMPT_PROBING,
            AttackId.GRAY_BOX,
            AttackId.PERMISSION_ESCALATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.MALICIOUS_CODE,
        name="Malicious Code",
        category=VulnerabilityCategory.TECHNICAL,
        description="Tests creation of malicious code",
        default_attacks=[AttackId.PROMPT_INJECTION, AttackId.ROLEPLAY, AttackId.BASE64],
        premium=True,
    ),
]

# =============================================================================
# BIAS & FAIRNESS VULNERABILITIES (Premium tier)
# =============================================================================

BIAS_FAIRNESS_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.BIAS_AGE,
        name="Age Bias",
        category=VulnerabilityCategory.BIAS_FAIRNESS,
        description="Age-related bias detection",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.BIAS_GENDER,
        name="Gender Bias",
        category=VulnerabilityCategory.BIAS_FAIRNESS,
        description="Gender-related bias detection",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.BIAS_RACE,
        name="Race Bias",
        category=VulnerabilityCategory.BIAS_FAIRNESS,
        description="Race-related bias detection",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.BIAS_DISABILITY,
        name="Disability Bias",
        category=VulnerabilityCategory.BIAS_FAIRNESS,
        description="Disability-related bias detection",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.BIAS_RELIGION,
        name="Religious Bias",
        category=VulnerabilityCategory.BIAS_FAIRNESS,
        description="Tests handling of religious content and bias",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.BIAS_POLITICAL,
        name="Political Bias",
        category=VulnerabilityCategory.BIAS_FAIRNESS,
        description="Tests handling of political content and bias",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.GOAL_REDIRECTION,
        ],
        premium=True,
    ),
]

# =============================================================================
# PROMPT SECURITY VULNERABILITIES
# =============================================================================

PROMPT_SECURITY_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.PROMPT_EXTRACTION,
        name="System Prompt Disclosure",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests for system prompt disclosure vulnerabilities",
        default_attacks=[
            AttackId.PROMPT_PROBING,
            AttackId.SYSTEM_OVERRIDE,
            AttackId.GRAY_BOX,
            AttackId.BASE64,
            AttackId.ROT13,
            # Note: social-engineering-prompt-extraction is a premium multi-turn attack
        ],
    ),
    VulnerabilityDef(
        id=VulnerabilityId.PROMPT_OVERRIDE,
        name="System Prompt Override",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests for system prompt override vulnerabilities",
        default_attacks=[
            AttackId.SYSTEM_OVERRIDE,
            AttackId.PROMPT_INJECTION,
            AttackId.CONTEXT_POISONING,
        ],
    ),
    VulnerabilityDef(
        id=VulnerabilityId.INDIRECT_INJECTION,
        name="Indirect Prompt Injection",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests for injection vulnerabilities via untrusted variables",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.CONTEXT_POISONING,
            AttackId.INPUT_BYPASS,
            AttackId.HTML_INDIRECT_PROMPT_INJECTION,
        ],
    ),
    VulnerabilityDef(
        id=VulnerabilityId.ASCII_SMUGGLING,
        name="ASCII Smuggling",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests vulnerability to Unicode tag-based instruction "
        "smuggling attacks",
        default_attacks=[
            AttackId.BASE64,
            AttackId.ROT13,
            AttackId.LEETSPEAK,
            AttackId.INPUT_BYPASS,
        ],
    ),
    VulnerabilityDef(
        id=VulnerabilityId.SPECIAL_TOKEN_INJECTION,
        name="Special Token Injection",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests vulnerability to token injection attacks using "
        "format-specific delimiters",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.INPUT_BYPASS,
            AttackId.BASE64,
        ],
    ),
    VulnerabilityDef(
        id=VulnerabilityId.PLINY_INJECTIONS,
        name="Pliny Prompt Injections",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests handling of Pliny prompt injections",
        default_attacks=[AttackId.PROMPT_INJECTION, AttackId.CONTEXT_POISONING],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.CONTEXT_COMPLIANCE,
        name="Context Compliance Attack",
        category=VulnerabilityCategory.PROMPT_SECURITY,
        description="Tests for vulnerability to Context Compliance Attacks "
        "using fabricated conversation history",
        default_attacks=[AttackId.CONTEXT_POISONING, AttackId.PROMPT_INJECTION],
        premium=True,
    ),
]

# =============================================================================
# ACCESS CONTROL VULNERABILITIES (Premium tier)
# =============================================================================

ACCESS_CONTROL_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.RBAC,
        name="RBAC Implementation",
        category=VulnerabilityCategory.ACCESS_CONTROL,
        description="Tests role-based access control implementation",
        default_attacks=[
            AttackId.PERMISSION_ESCALATION,
            AttackId.GRAY_BOX,
            AttackId.PROMPT_INJECTION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.BOLA,
        name="Object-Level Authorization Bypass",
        category=VulnerabilityCategory.ACCESS_CONTROL,
        description="Tests for broken object-level authorization "
        "vulnerabilities (OWASP API 1)",
        default_attacks=[
            AttackId.PERMISSION_ESCALATION,
            AttackId.GRAY_BOX,
            AttackId.INPUT_BYPASS,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.BFLA,
        name="Function-Level Authorization Bypass",
        category=VulnerabilityCategory.ACCESS_CONTROL,
        description="Tests for broken function-level authorization "
        "vulnerabilities (OWASP API 5)",
        default_attacks=[
            AttackId.PERMISSION_ESCALATION,
            AttackId.GRAY_BOX,
            AttackId.PROMPT_INJECTION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.EXCESSIVE_AGENCY,
        name="Excessive Agency",
        category=VulnerabilityCategory.ACCESS_CONTROL,
        description="Tests for unauthorized actions beyond defined system boundaries",
        default_attacks=[
            AttackId.ROLEPLAY,
            AttackId.GOAL_REDIRECTION,
            AttackId.PERMISSION_ESCALATION,
            AttackId.CONTEXT_POISONING,
        ],
        premium=True,
    ),
]

# =============================================================================
# BUSINESS LOGIC VULNERABILITIES (Premium tier)
# =============================================================================

BUSINESS_LOGIC_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.UNAUTHORIZED_COMMITMENTS,
        name="Unauthorized Commitments",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests for unauthorized contractual commitments and legal exposure",
        default_attacks=[
            AttackId.ROLEPLAY,
            AttackId.GOAL_REDIRECTION,
            AttackId.CONTEXT_POISONING,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.UNAUTHORIZED_ADVICE,
        name="Unauthorized Advice",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests handling of unauthorized professional advice",
        default_attacks=[
            AttackId.ROLEPLAY,
            AttackId.PROMPT_INJECTION,
            AttackId.GOAL_REDIRECTION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.COMPETITORS,
        name="Competitors",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests for unauthorized competitor mentions and endorsements",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.GOAL_REDIRECTION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.IMITATION,
        name="Entity Impersonation",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests handling of unauthorized impersonation of entities",
        default_attacks=[
            AttackId.ROLEPLAY,
            AttackId.CONTEXT_POISONING,
            AttackId.PROMPT_INJECTION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.GOAL_MISALIGNMENT,
        name="Goal Misalignment (Goodhart's Law)",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests whether AI systems recognize when optimizing proxy "
        "metrics might not align with true goals",
        default_attacks=[
            AttackId.GOAL_REDIRECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.OFF_TOPIC,
        name="Off-Topic Manipulation",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests whether AI systems can be manipulated to go off-topic "
        "from their intended purpose",
        default_attacks=[
            AttackId.GOAL_REDIRECTION,
            AttackId.CONTEXT_POISONING,
            AttackId.ROLEPLAY,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.HIJACKING,
        name="Resource Hijacking",
        category=VulnerabilityCategory.BUSINESS_LOGIC,
        description="Tests for unauthorized resource usage and purpose deviation",
        default_attacks=[
            AttackId.GOAL_REDIRECTION,
            AttackId.PERMISSION_ESCALATION,
            AttackId.ROLEPLAY,
        ],
        premium=True,
    ),
]

# =============================================================================
# INTELLECTUAL PROPERTY VULNERABILITIES (Premium tier)
# =============================================================================

IP_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.IP_VIOLATIONS,
        name="IP Violations",
        category=VulnerabilityCategory.INTELLECTUAL_PROPERTY,
        description="Tests handling of intellectual property violations",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.GOAL_REDIRECTION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.IP_THEFT,
        name="IP Theft",
        category=VulnerabilityCategory.INTELLECTUAL_PROPERTY,
        description="Tests handling of IP theft and violations",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.CONTEXT_POISONING,
        ],
        premium=True,
    ),
]

# =============================================================================
# INFORMATION QUALITY VULNERABILITIES (Premium tier)
# =============================================================================

INFO_QUALITY_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.HALLUCINATION,
        name="Hallucination",
        category=VulnerabilityCategory.INFORMATION_QUALITY,
        description="Tests for fabrication of false or misleading information",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.GOAL_REDIRECTION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.UNVERIFIABLE_CLAIMS,
        name="Unverifiable Claims",
        category=VulnerabilityCategory.INFORMATION_QUALITY,
        description="Tests for claims that cannot be verified or fact-checked",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.MISINFORMATION_DISINFORMATION,
        name="Disinformation Campaigns",
        category=VulnerabilityCategory.INFORMATION_QUALITY,
        description="Tests handling of false information campaigns",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.CONTEXT_POISONING,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.OVERRELIANCE,
        name="Overreliance",
        category=VulnerabilityCategory.INFORMATION_QUALITY,
        description="Tests for overreliance on system assumptions",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.CONTEXT_POISONING,
            AttackId.GRAY_BOX,
        ],
        premium=True,
    ),
]

# =============================================================================
# COMPLIANCE VULNERABILITIES (Premium tier)
# =============================================================================

COMPLIANCE_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.COPPA,
        name="COPPA Compliance",
        category=VulnerabilityCategory.COMPLIANCE,
        description="Tests for COPPA (Children's Online Privacy Protection Act) "
        "compliance violations",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.GOAL_REDIRECTION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.FERPA,
        name="FERPA Compliance",
        category=VulnerabilityCategory.COMPLIANCE,
        description="Tests for compliance with Family Educational Rights and "
        "Privacy Act",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.PERMISSION_ESCALATION,
            AttackId.GRAY_BOX,
        ],
        premium=True,
    ),
]

# =============================================================================
# SPECIALIZED THREATS (Premium tier)
# =============================================================================

SPECIALIZED_THREATS_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.CYBERCRIME,
        name="Cybercrime",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of cybercrime-related content",
        default_attacks=[AttackId.PROMPT_INJECTION, AttackId.ROLEPLAY, AttackId.BASE64],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.WMD_CONTENT,
        name="WMD Content",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of WMD-related content",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.WEAPONS_CONTENT,
        name="Weapons Content",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of weapons-related content",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.MATH_PROBLEM,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.IED_CONTENT,
        name="Improvised Explosive Devices",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of Improvised Explosive Devices",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.DRUGS,
        name="Drug-Related Content",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of illegal drug-related content",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.METHAMPHETAMINE,
        name="Methamphetamine Content",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of methamphetamine-related content",
        default_attacks=[AttackId.PROMPT_INJECTION, AttackId.ROLEPLAY, AttackId.BASE64],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.EXTREMISM,
        name="Extremist Content",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of extremist content and recruitment",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.CONTEXT_POISONING,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.ILLEGAL_ACTIVITY,
        name="Illegal Activity",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of general illegal activities",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.GOAL_REDIRECTION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.NON_VIOLENT_CRIME,
        name="Non-Violent Crime",
        category=VulnerabilityCategory.SPECIALIZED_THREATS,
        description="Tests handling of non-violent criminal content",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.ROLEPLAY,
            AttackId.SEMANTIC_MANIPULATION,
        ],
        premium=True,
    ),
]

# =============================================================================
# AGENT-SPECIFIC VULNERABILITIES (Premium tier)
# =============================================================================

AGENT_SPECIFIC_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.MEMORY_POISONING,
        name="Agentic Memory Poisoning",
        category=VulnerabilityCategory.AGENT_SPECIFIC,
        description="Tests whether an agent is vulnerable to memory poisoning attacks",
        default_attacks=[AttackId.CONTEXT_POISONING, AttackId.PROMPT_INJECTION],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.RAG_POISONING,
        name="RAG Poisoning",
        category=VulnerabilityCategory.AGENT_SPECIFIC,
        description="Tests for vulnerabilities to RAG retrieval poisoning attacks",
        default_attacks=[AttackId.CONTEXT_POISONING, AttackId.PROMPT_INJECTION],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.RAG_EXFILTRATION,
        name="RAG Document Exfiltration",
        category=VulnerabilityCategory.AGENT_SPECIFIC,
        description="Tests for RAG document exfiltration",
        default_attacks=[
            AttackId.PROMPT_INJECTION,
            AttackId.PROMPT_PROBING,
            AttackId.GRAY_BOX,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.TOOL_DISCOVERY,
        name="Tool Discovery",
        category=VulnerabilityCategory.AGENT_SPECIFIC,
        description="Tests for enumeration of available tools and function calls",
        default_attacks=[
            AttackId.PROMPT_PROBING,
            AttackId.GRAY_BOX,
            AttackId.PROMPT_INJECTION,
        ],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.MCP_VULNERABILITIES,
        name="Model Context Protocol",
        category=VulnerabilityCategory.AGENT_SPECIFIC,
        description="Tests for vulnerabilities to Model Context Protocol (MCP) attacks",
        default_attacks=[AttackId.PROMPT_INJECTION, AttackId.CONTEXT_POISONING],
        premium=True,
    ),
]

# =============================================================================
# RESOURCE ATTACK VULNERABILITIES (Premium tier)
# =============================================================================

RESOURCE_ATTACK_VULNERABILITIES = [
    VulnerabilityDef(
        id=VulnerabilityId.UNBOUNDED_CONSUMPTION,
        name="Unbounded Consumption",
        category=VulnerabilityCategory.RESOURCE_ATTACKS,
        description="Tests for resource exhaustion vulnerabilities",
        default_attacks=[AttackId.PROMPT_INJECTION, AttackId.GOAL_REDIRECTION],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.REASONING_DOS,
        name="Reasoning DoS",
        category=VulnerabilityCategory.RESOURCE_ATTACKS,
        description="Tests for vulnerabilities to computational resource exhaustion "
        "through excessive reasoning patterns",
        default_attacks=[AttackId.PROMPT_INJECTION, AttackId.MATH_PROBLEM],
        premium=True,
    ),
    VulnerabilityDef(
        id=VulnerabilityId.DIVERGENT_REPETITION,
        name="Divergent Repetition",
        category=VulnerabilityCategory.RESOURCE_ATTACKS,
        description="Tests for training data leaks through repetitive pattern "
        "exploitation that causes model divergence",
        default_attacks=[AttackId.PROMPT_INJECTION, AttackId.GOAL_REDIRECTION],
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
        VulnerabilityId.PROMPT_EXTRACTION,
        VulnerabilityId.PROMPT_OVERRIDE,
        VulnerabilityId.INDIRECT_INJECTION,
        VulnerabilityId.ASCII_SMUGGLING,
        VulnerabilityId.SPECIAL_TOKEN_INJECTION,
        # PII Protection (free)
        VulnerabilityId.PII_DIRECT,
        VulnerabilityId.PII_API_DB,
        VulnerabilityId.PII_SESSION,
        VulnerabilityId.CROSS_SESSION_LEAKAGE,
        VulnerabilityId.PRIVACY_VIOLATION,
    ]


def get_full_scan_vulnerabilities() -> List[str]:
    """
    Get all vulnerability IDs for full scan.

    Returns all vulnerability IDs including premium ones.
    """
    return list(VULNERABILITY_CATALOG.keys())
