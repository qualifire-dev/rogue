"""
Framework Mappings for Red Teaming.

Contains framework definitions with their mapped vulnerabilities.
These mappings are used for compliance report generation only -
they do not drive test execution.
"""

from enum import Enum
from typing import Dict, List, Optional

from ..models import FrameworkDef
from .vulnerabilities import VulnerabilityId


class FrameworkId(str, Enum):
    """Enum of all framework IDs for type safety."""

    OWASP_LLM = "owasp-llm"
    MITRE_ATLAS = "mitre-atlas"
    NIST_AI = "nist-ai"
    ISO_42001 = "iso-42001"
    EU_AI_ACT = "eu-ai-act"
    GDPR = "gdpr"
    OWASP_API = "owasp-api"
    BASIC_SECURITY = "basic-security"


# =============================================================================
# FRAMEWORK DEFINITIONS
# =============================================================================

OWASP_LLM_TOP_10 = FrameworkDef(
    id=FrameworkId.OWASP_LLM,
    name="OWASP LLM Top 10",
    description="OWASP Top 10 for LLM Applications 2025",
    vulnerabilities=[
        # LLM01: Prompt Injection
        VulnerabilityId.PROMPT_EXTRACTION,
        VulnerabilityId.PROMPT_OVERRIDE,
        VulnerabilityId.INDIRECT_INJECTION,
        VulnerabilityId.ASCII_SMUGGLING,
        # LLM02: Sensitive Information Disclosure
        VulnerabilityId.PII_DIRECT,
        VulnerabilityId.PII_API_DB,
        VulnerabilityId.PII_SESSION,
        VulnerabilityId.PII_SOCIAL,
        VulnerabilityId.CROSS_SESSION_LEAKAGE,
        # LLM03: Supply Chain
        VulnerabilityId.IP_VIOLATIONS,
        # LLM04: Data and Model Poisoning
        VulnerabilityId.MEMORY_POISONING,
        VulnerabilityId.RAG_POISONING,
        # LLM05: Improper Output Handling
        VulnerabilityId.SQL_INJECTION,
        VulnerabilityId.SHELL_INJECTION,
        VulnerabilityId.MALICIOUS_CODE,
        # LLM06: Excessive Agency
        VulnerabilityId.EXCESSIVE_AGENCY,
        VulnerabilityId.RBAC,
        VulnerabilityId.BOLA,
        VulnerabilityId.BFLA,
        # LLM07: System Prompt Leakage
        VulnerabilityId.PROMPT_EXTRACTION,
        # LLM08: Vector and Embedding Weaknesses
        VulnerabilityId.RAG_EXFILTRATION,
        # LLM09: Misinformation
        VulnerabilityId.HALLUCINATION,
        VulnerabilityId.UNVERIFIABLE_CLAIMS,
        VulnerabilityId.MISINFORMATION_DISINFORMATION,
        VulnerabilityId.OVERRELIANCE,
        # LLM10: Unbounded Consumption
        VulnerabilityId.UNBOUNDED_CONSUMPTION,
        VulnerabilityId.REASONING_DOS,
        VulnerabilityId.DIVERGENT_REPETITION,
        # Content safety
        VulnerabilityId.HATE_SPEECH,
        VulnerabilityId.EXPLICIT_CONTENT,
        VulnerabilityId.VIOLENT_CRIME,
        VulnerabilityId.SEXUAL_CRIME,
        VulnerabilityId.CHILD_EXPLOITATION,
        VulnerabilityId.HARASSMENT,
        VulnerabilityId.PERSONAL_ATTACKS,
        VulnerabilityId.PROFANITY,
        VulnerabilityId.GRAPHIC_CONTENT,
        VulnerabilityId.SELF_HARM,
        VulnerabilityId.DANGEROUS_ACTIVITY,
        # Bias
        VulnerabilityId.BIAS_AGE,
        VulnerabilityId.BIAS_GENDER,
        VulnerabilityId.BIAS_RACE,
        VulnerabilityId.BIAS_DISABILITY,
        # Technical
        VulnerabilityId.SSRF,
        VulnerabilityId.DEBUG_ACCESS,
        # Specialized threats
        VulnerabilityId.CYBERCRIME,
        VulnerabilityId.WMD_CONTENT,
        VulnerabilityId.WEAPONS_CONTENT,
        VulnerabilityId.IED_CONTENT,
        VulnerabilityId.DRUGS,
        VulnerabilityId.METHAMPHETAMINE,
        VulnerabilityId.EXTREMISM,
        VulnerabilityId.ILLEGAL_ACTIVITY,
        VulnerabilityId.NON_VIOLENT_CRIME,
        VulnerabilityId.IP_THEFT,
        VulnerabilityId.UNAUTHORIZED_ADVICE,
    ],
)

MITRE_ATLAS = FrameworkDef(
    id=FrameworkId.MITRE_ATLAS,
    name="MITRE ATLAS",
    description="MITRE Adversarial Threat Landscape for AI Systems",
    vulnerabilities=[
        # Prompt/Input attacks
        VulnerabilityId.ASCII_SMUGGLING,
        VulnerabilityId.PROMPT_EXTRACTION,
        VulnerabilityId.PROMPT_OVERRIDE,
        VulnerabilityId.INDIRECT_INJECTION,
        # Privacy
        VulnerabilityId.PRIVACY_VIOLATION,
        VulnerabilityId.PII_API_DB,
        VulnerabilityId.PII_DIRECT,
        VulnerabilityId.PII_SESSION,
        VulnerabilityId.PII_SOCIAL,
        # System compromise
        VulnerabilityId.EXCESSIVE_AGENCY,
        VulnerabilityId.IP_VIOLATIONS,
        # Content safety
        VulnerabilityId.CHILD_EXPLOITATION,
        VulnerabilityId.WMD_CONTENT,
        VulnerabilityId.GRAPHIC_CONTENT,
        VulnerabilityId.CYBERCRIME,
        VulnerabilityId.HARASSMENT,
        VulnerabilityId.HATE_SPEECH,
        VulnerabilityId.ILLEGAL_ACTIVITY,
        VulnerabilityId.METHAMPHETAMINE,
        VulnerabilityId.DRUGS,
        VulnerabilityId.IP_THEFT,
        VulnerabilityId.WEAPONS_CONTENT,
        VulnerabilityId.PERSONAL_ATTACKS,
        VulnerabilityId.PROFANITY,
        VulnerabilityId.EXTREMISM,
        VulnerabilityId.NON_VIOLENT_CRIME,
        VulnerabilityId.MISINFORMATION_DISINFORMATION,
        VulnerabilityId.SELF_HARM,
        VulnerabilityId.EXPLICIT_CONTENT,
        VulnerabilityId.UNAUTHORIZED_ADVICE,
        VulnerabilityId.DANGEROUS_ACTIVITY,
        VulnerabilityId.IED_CONTENT,
        # Technical
        VulnerabilityId.DEBUG_ACCESS,
        VulnerabilityId.SHELL_INJECTION,
        VulnerabilityId.SQL_INJECTION,
        VulnerabilityId.RBAC,
        VulnerabilityId.MALICIOUS_CODE,
        VulnerabilityId.SEXUAL_CRIME,
        VulnerabilityId.VIOLENT_CRIME,
        VulnerabilityId.SSRF,
        # Information quality
        VulnerabilityId.HALLUCINATION,
        # Business logic
        VulnerabilityId.HIJACKING,
        VulnerabilityId.IMITATION,
        VulnerabilityId.COMPETITORS,
    ],
)

NIST_AI_RMF = FrameworkDef(
    id=FrameworkId.NIST_AI,
    name="NIST AI RMF",
    description="NIST AI Risk Management Framework",
    vulnerabilities=[
        # Excessive agency
        VulnerabilityId.EXCESSIVE_AGENCY,
        # Information integrity
        VulnerabilityId.MISINFORMATION_DISINFORMATION,
        # Privacy
        VulnerabilityId.PRIVACY_VIOLATION,
        VulnerabilityId.PII_API_DB,
        VulnerabilityId.PII_DIRECT,
        VulnerabilityId.PII_SESSION,
        VulnerabilityId.PII_SOCIAL,
        # Safety
        VulnerabilityId.WMD_CONTENT,
        VulnerabilityId.WEAPONS_CONTENT,
        VulnerabilityId.DANGEROUS_ACTIVITY,
        VulnerabilityId.CYBERCRIME,
        # Technical
        VulnerabilityId.SHELL_INJECTION,
        VulnerabilityId.SQL_INJECTION,
        VulnerabilityId.BFLA,
        VulnerabilityId.BOLA,
        VulnerabilityId.RBAC,
        # Content
        VulnerabilityId.HARASSMENT,
        VulnerabilityId.HATE_SPEECH,
        VulnerabilityId.PERSONAL_ATTACKS,
    ],
)

ISO_42001 = FrameworkDef(
    id=FrameworkId.ISO_42001,
    name="ISO/IEC 42001",
    description="ISO/IEC 42001 AI Management System",
    vulnerabilities=[
        # Governance
        VulnerabilityId.EXCESSIVE_AGENCY,
        VulnerabilityId.OVERRELIANCE,
        # Bias
        VulnerabilityId.BIAS_DISABILITY,
        VulnerabilityId.BIAS_GENDER,
        VulnerabilityId.BIAS_AGE,
        VulnerabilityId.BIAS_RACE,
        VulnerabilityId.BIAS_POLITICAL,
        VulnerabilityId.BIAS_RELIGION,
        # Content safety
        VulnerabilityId.HATE_SPEECH,
        # Privacy
        VulnerabilityId.PRIVACY_VIOLATION,
        VulnerabilityId.PII_API_DB,
        VulnerabilityId.PII_DIRECT,
        VulnerabilityId.PII_SESSION,
        VulnerabilityId.PII_SOCIAL,
        # Security
        VulnerabilityId.ASCII_SMUGGLING,
        VulnerabilityId.PROMPT_EXTRACTION,
        VulnerabilityId.SHELL_INJECTION,
        VulnerabilityId.SQL_INJECTION,
        VulnerabilityId.DEBUG_ACCESS,
        VulnerabilityId.SSRF,
        # Safety
        VulnerabilityId.WMD_CONTENT,
        VulnerabilityId.CHILD_EXPLOITATION,
        VulnerabilityId.CYBERCRIME,
        VulnerabilityId.MISINFORMATION_DISINFORMATION,
        VulnerabilityId.VIOLENT_CRIME,
        VulnerabilityId.MALICIOUS_CODE,
        # Information quality
        VulnerabilityId.HALLUCINATION,
        VulnerabilityId.UNVERIFIABLE_CLAIMS,
        # Business
        VulnerabilityId.HIJACKING,
        VulnerabilityId.IMITATION,
    ],
)

EU_AI_ACT = FrameworkDef(
    id=FrameworkId.EU_AI_ACT,
    name="EU AI Act",
    description="European Union Artificial Intelligence Act",
    vulnerabilities=[
        # High-risk requirements
        VulnerabilityId.EXCESSIVE_AGENCY,
        VulnerabilityId.MISINFORMATION_DISINFORMATION,
        VulnerabilityId.OVERRELIANCE,
        # Privacy (GDPR alignment)
        VulnerabilityId.PII_DIRECT,
        VulnerabilityId.PII_SESSION,
        VulnerabilityId.PRIVACY_VIOLATION,
        VulnerabilityId.PII_API_DB,
        # Technical safety
        VulnerabilityId.SHELL_INJECTION,
        VulnerabilityId.SQL_INJECTION,
        VulnerabilityId.SSRF,
        # Non-discrimination
        VulnerabilityId.HATE_SPEECH,
        # Information quality
        VulnerabilityId.HALLUCINATION,
        # Business
        VulnerabilityId.HIJACKING,
        VulnerabilityId.IMITATION,
    ],
)

GDPR = FrameworkDef(
    id=FrameworkId.GDPR,
    name="GDPR",
    description="General Data Protection Regulation",
    vulnerabilities=[
        # Data protection
        VulnerabilityId.PRIVACY_VIOLATION,
        VulnerabilityId.PII_API_DB,
        VulnerabilityId.PII_DIRECT,
        VulnerabilityId.PII_SESSION,
        VulnerabilityId.PII_SOCIAL,
        VulnerabilityId.CROSS_SESSION_LEAKAGE,
        # Information integrity
        VulnerabilityId.MISINFORMATION_DISINFORMATION,
        # Non-discrimination
        VulnerabilityId.BIAS_DISABILITY,
        VulnerabilityId.BIAS_GENDER,
        VulnerabilityId.BIAS_AGE,
        VulnerabilityId.BIAS_RACE,
        VulnerabilityId.HATE_SPEECH,
        # Access control
        VulnerabilityId.RBAC,
        VulnerabilityId.BOLA,
        VulnerabilityId.BFLA,
        # Security
        VulnerabilityId.PROMPT_EXTRACTION,
        VulnerabilityId.SHELL_INJECTION,
        VulnerabilityId.SQL_INJECTION,
        VulnerabilityId.DEBUG_ACCESS,
        VulnerabilityId.SSRF,
        # Other
        VulnerabilityId.OVERRELIANCE,
        VulnerabilityId.CYBERCRIME,
        VulnerabilityId.HALLUCINATION,
    ],
)

OWASP_API_TOP_10 = FrameworkDef(
    id=FrameworkId.OWASP_API,
    name="OWASP API Top 10",
    description="OWASP API Security Top 10",
    vulnerabilities=[
        # API1: Broken Object Level Authorization
        VulnerabilityId.BOLA,
        # API2: Broken Authentication
        VulnerabilityId.RBAC,
        # API3: Broken Object Property Level Authorization
        VulnerabilityId.BFLA,
        # API4: Unrestricted Resource Consumption
        VulnerabilityId.UNBOUNDED_CONSUMPTION,
        # API5: Broken Function Level Authorization
        VulnerabilityId.EXCESSIVE_AGENCY,
        # API6: Unrestricted Access to Sensitive Business Flows
        VulnerabilityId.OVERRELIANCE,
        # API7: Server Side Request Forgery
        VulnerabilityId.SSRF,
        # API8: Security Misconfiguration
        VulnerabilityId.DEBUG_ACCESS,
        # API9: Improper Inventory Management
        VulnerabilityId.PRIVACY_VIOLATION,
        VulnerabilityId.PII_API_DB,
        VulnerabilityId.PII_SESSION,
        # API10: Unsafe Consumption of APIs
        VulnerabilityId.MISINFORMATION_DISINFORMATION,
        VulnerabilityId.SHELL_INJECTION,
        VulnerabilityId.SQL_INJECTION,
        VulnerabilityId.UNAUTHORIZED_ADVICE,
    ],
)

BASIC_SECURITY = FrameworkDef(
    id=FrameworkId.BASIC_SECURITY,
    name="Basic Security",
    description="Basic security testing for AI agents",
    vulnerabilities=[
        # Prompt security
        VulnerabilityId.PROMPT_EXTRACTION,
        VulnerabilityId.PROMPT_OVERRIDE,
        # PII
        VulnerabilityId.PII_DIRECT,
        # Technical
        VulnerabilityId.SQL_INJECTION,
        VulnerabilityId.SHELL_INJECTION,
        # Agency
        VulnerabilityId.EXCESSIVE_AGENCY,
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
