"""
Core data models for the red teaming system.

These models define the structure for vulnerabilities, attacks, and framework mappings
that drive the vulnerability-centric red teaming approach.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class Severity(str, Enum):
    """Severity levels for vulnerabilities."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ScanType(str, Enum):
    """Types of red team scans."""

    BASIC = "basic"  # Free tier - limited vulnerabilities/attacks
    FULL = "full"  # Premium - all vulnerabilities and attacks
    CUSTOM = "custom"  # User-selected vulnerabilities and attacks


class AttackCategory(str, Enum):
    """Categories of attack techniques."""

    SINGLE_TURN = "single_turn"
    MULTI_TURN = "multi_turn"
    AGENTIC = "agentic"


class VulnerabilityCategory(str, Enum):
    """Categories of vulnerabilities."""

    CONTENT_SAFETY = "content_safety"
    PII_PROTECTION = "pii_protection"
    TECHNICAL = "technical"
    BIAS_FAIRNESS = "bias_fairness"
    PROMPT_SECURITY = "prompt_security"
    ACCESS_CONTROL = "access_control"
    BUSINESS_LOGIC = "business_logic"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    INFORMATION_QUALITY = "information_quality"
    COMPLIANCE = "compliance"
    SPECIALIZED_THREATS = "specialized_threats"
    AGENT_SPECIFIC = "agent_specific"
    RESOURCE_ATTACKS = "resource_attacks"


@dataclass
class VulnerabilityDef:
    """
    Definition of a vulnerability type that can be tested.

    Attributes:
        id: Unique identifier (e.g., "pii-direct", "prompt-injection")
        name: Human-readable display name
        category: Category grouping for UI organization
        description: Detailed description of what this vulnerability tests
        default_attacks: List of attack IDs that are effective for this vulnerability
        premium: Whether this requires a Qualifire API key
    """

    id: str
    name: str
    category: VulnerabilityCategory
    description: str
    default_attacks: List[str] = field(default_factory=list)
    premium: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "default_attacks": self.default_attacks,
            "premium": self.premium,
        }


@dataclass
class AttackDef:
    """
    Definition of an attack technique.

    Attributes:
        id: Unique identifier (e.g., "base64", "goat", "hydra")
        name: Human-readable display name
        category: Attack category (single-turn, multi-turn, agentic)
        description: Description of the attack technique
        premium: Whether this requires a Qualifire API key
    """

    id: str
    name: str
    category: AttackCategory
    description: str = ""
    premium: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "premium": self.premium,
        }


@dataclass
class FrameworkDef:
    """
    Definition of a compliance framework.

    Frameworks are used for report generation only - they map vulnerabilities
    to compliance requirements for reporting purposes.

    Attributes:
        id: Unique identifier (e.g., "owasp-llm", "mitre-atlas")
        name: Human-readable display name
        description: Description of the framework
        vulnerabilities: List of vulnerability IDs mapped to this framework
    """

    id: str
    name: str
    description: str
    vulnerabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "vulnerabilities": self.vulnerabilities,
        }


# Pydantic models for API communication


class RedTeamConfig(BaseModel):
    """Configuration for red team evaluation."""

    scan_type: ScanType = Field(
        default=ScanType.BASIC,
        description="Type of scan: basic, full, or custom",
    )
    vulnerabilities: List[str] = Field(
        default_factory=list,
        description="List of vulnerability IDs to test",
    )
    attacks: List[str] = Field(
        default_factory=list,
        description="List of attack IDs to use",
    )
    attacks_per_vulnerability: int = Field(
        default=3,
        description="Number of attack attempts per vulnerability",
    )
    frameworks: List[str] = Field(
        default_factory=list,
        description=(
            "Framework IDs for report mapping " "(e.g., 'owasp-llm', 'mitre-atlas')"
        ),
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducible tests",
    )

    @model_validator(mode="after")
    def set_default_frameworks(self) -> "RedTeamConfig":
        """Set default frameworks based on scan type if none provided."""
        # If frameworks are explicitly provided, keep them
        if self.frameworks:
            return self

        # Set default frameworks based on scan type
        if self.scan_type == ScanType.BASIC:
            self.frameworks = ["basic-security"]
        elif self.scan_type == ScanType.FULL:
            self.frameworks = ["owasp-llm", "mitre-atlas", "basic-security"]
        # For CUSTOM, leave frameworks empty

        return self


class VulnerabilityResult(BaseModel):
    """Result of testing a single vulnerability."""

    vulnerability_id: str = Field(description="ID of the vulnerability tested")
    vulnerability_name: str = Field(description="Name of the vulnerability")
    passed: bool = Field(description="Whether the agent resisted the vulnerability")
    attacks_attempted: int = Field(description="Number of attacks attempted")
    attacks_successful: int = Field(
        description="Number of attacks that found vulnerabilities",
    )
    severity: Optional[Severity] = Field(
        default=None,
        description="Severity if vulnerability found",
    )
    cvss_score: Optional[float] = Field(
        default=None,
        description="CVSS-like risk score (0-10) for the vulnerability if exploited",
    )
    risk_level: Optional[str] = Field(
        default=None,
        description="Risk level classification: critical, high, medium, low",
    )
    risk_components: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed risk score components (impact, exploitability, etc.)",
    )
    details: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed results per attack",
    )


class FrameworkCompliance(BaseModel):
    """Compliance status for a single framework."""

    framework_id: str = Field(description="ID of the framework")
    framework_name: str = Field(description="Name of the framework")
    compliance_score: float = Field(
        description="Compliance score from 0-100",
    )
    vulnerabilities_tested: int = Field(
        description="Number of mapped vulnerabilities tested",
    )
    vulnerabilities_passed: int = Field(
        description="Number of vulnerabilities that passed",
    )
    vulnerability_breakdown: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Per-vulnerability status for this framework",
    )


class AttackStats(BaseModel):
    """Statistics for a single attack technique."""

    attack_id: str = Field(description="ID of the attack")
    attack_name: str = Field(description="Name of the attack")
    times_used: int = Field(default=0, description="Number of times attack was used")
    success_count: int = Field(
        default=0,
        description="Number of successful exploits",
    )
    success_rate: float = Field(
        default=0.0,
        description="Success rate (success_count / times_used)",
    )
    vulnerabilities_tested: List[str] = Field(
        default_factory=list,
        description="List of vulnerability IDs this attack was used against",
    )


class RedTeamResults(BaseModel):
    """Complete results from a red team evaluation."""

    vulnerability_results: List[VulnerabilityResult] = Field(
        default_factory=list,
        description="Results for each vulnerability tested",
    )
    framework_compliance: Dict[str, FrameworkCompliance] = Field(
        default_factory=dict,
        description="Compliance results per framework",
    )
    attack_statistics: Dict[str, AttackStats] = Field(
        default_factory=dict,
        description="Statistics per attack technique",
    )
    total_vulnerabilities_tested: int = Field(
        default=0,
        description="Total number of vulnerabilities tested",
    )
    total_vulnerabilities_found: int = Field(
        default=0,
        description="Total number of vulnerabilities exploited",
    )
    overall_score: float = Field(
        default=100.0,
        description="Overall security score from 0-100",
    )
    csv_export_path: Optional[str] = Field(
        default=None,
        description="Path to CSV export of all conversations",
    )
    conversations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="All conversation logs for export",
    )


# =============================================================================
# COMPREHENSIVE REPORT MODELS
# =============================================================================


class ReportHighlights(BaseModel):
    """High-level summary statistics for the report."""

    critical_count: int = Field(
        default=0,
        description="Number of critical vulnerabilities",
    )
    high_count: int = Field(default=0, description="Number of high vulnerabilities")
    medium_count: int = Field(default=0, description="Number of medium vulnerabilities")
    low_count: int = Field(default=0, description="Number of low vulnerabilities")
    total_vulnerabilities_tested: int = Field(
        default=0,
        description="Total vulnerabilities tested",
    )
    total_vulnerabilities_found: int = Field(
        default=0,
        description="Total vulnerabilities exploited",
    )
    overall_score: float = Field(
        default=100.0,
        description="Overall security score (0-100)",
    )


class KeyFinding(BaseModel):
    """A key finding for the report (top critical vulnerability)."""

    vulnerability_id: str = Field(description="Vulnerability ID")
    vulnerability_name: str = Field(description="Vulnerability name")
    cvss_score: float = Field(description="CVSS risk score (0-10)")
    severity: Severity = Field(description="Severity level")
    summary: str = Field(description="LLM-generated summary of what happened")
    attack_ids: List[str] = Field(
        default_factory=list,
        description="Attack IDs that exploited this",
    )
    success_rate: float = Field(
        default=0.0,
        description="Success rate of attacks (0-1)",
    )


class VulnerabilityTableRow(BaseModel):
    """Row in the vulnerability breakdown table."""

    vulnerability_id: str = Field(description="Vulnerability ID")
    vulnerability_name: str = Field(description="Vulnerability name")
    severity: Optional[Severity] = Field(default=None, description="Severity if failed")
    attacks_used: List[str] = Field(
        default_factory=list,
        description="List of attack IDs used",
    )
    attacks_attempted: int = Field(default=0, description="Total attacks attempted")
    attacks_successful: int = Field(default=0, description="Successful attacks")
    success_rate: float = Field(default=0.0, description="Success rate (0-100)")
    passed: bool = Field(description="Whether the vulnerability check passed")


class FrameworkCoverageCard(BaseModel):
    """Framework compliance card for the report."""

    framework_id: str = Field(description="Framework ID")
    framework_name: str = Field(description="Framework name")
    compliance_score: float = Field(description="Compliance score (0-100)")
    tested_count: int = Field(description="Number of vulnerabilities tested")
    total_count: int = Field(
        description="Total vulnerabilities mapped to this framework",
    )
    passed_count: int = Field(description="Number of vulnerabilities passed")
    status: str = Field(
        description="Status: excellent (>80), good (60-80), poor (<60)",
    )


class ReportMetadata(BaseModel):
    """Metadata for the red team report."""

    scan_date: str = Field(description="ISO timestamp of scan")
    scan_type: str = Field(description="Type of scan: basic, full, custom")
    frameworks_tested: List[str] = Field(
        default_factory=list,
        description="Framework IDs included",
    )
    attacks_used: List[str] = Field(
        default_factory=list,
        description="Attack IDs used",
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed if used",
    )


class RedTeamReport(BaseModel):
    """Comprehensive red team security report."""

    metadata: ReportMetadata = Field(description="Report metadata")
    highlights: ReportHighlights = Field(description="High-level summary statistics")
    key_findings: List[KeyFinding] = Field(
        default_factory=list,
        description="Top 5 most critical findings",
    )
    vulnerability_table: List[VulnerabilityTableRow] = Field(
        default_factory=list,
        description="Full vulnerability breakdown",
    )
    framework_coverage: List[FrameworkCoverageCard] = Field(
        default_factory=list,
        description="Framework compliance cards",
    )
    csv_conversations_path: Optional[str] = Field(
        default=None,
        description="Path to conversations CSV export",
    )
    csv_summary_path: Optional[str] = Field(
        default=None,
        description="Path to summary CSV export",
    )
