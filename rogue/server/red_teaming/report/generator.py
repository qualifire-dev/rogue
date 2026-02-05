"""
Compliance Report Generator for Red Teaming.

Generates reports from red team results by mapping vulnerability findings
to various security and compliance frameworks.
"""

import csv
import io
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

from loguru import logger

from ..catalog.framework_mappings import get_framework
from ..catalog.vulnerabilities import get_vulnerability
from ..models import (
    FrameworkCoverageCard,
    RedTeamReport,
    RedTeamResults,
    ReportHighlights,
    ReportMetadata,
    VulnerabilityTableRow,
)
from ..utils.workspace import get_csv_export_paths, save_to_file
from .key_findings import generate_key_findings


class FrameworkReport:
    """Report for a single compliance framework."""

    def __init__(
        self,
        framework_id: str,
        framework_name: str,
        compliance_score: float,
        categories_tested: int,
        categories_passed: int,
        vulnerability_breakdown: List[Dict[str, Any]],
        recommendations: List[str],
    ):
        self.framework_id = framework_id
        self.framework_name = framework_name
        self.compliance_score = compliance_score
        self.categories_tested = categories_tested
        self.categories_passed = categories_passed
        self.vulnerability_breakdown = vulnerability_breakdown
        self.recommendations = recommendations

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "framework_id": self.framework_id,
            "framework_name": self.framework_name,
            "compliance_score": self.compliance_score,
            "categories_tested": self.categories_tested,
            "categories_passed": self.categories_passed,
            "vulnerability_breakdown": self.vulnerability_breakdown,
            "recommendations": self.recommendations,
        }


class ComplianceReportGenerator:
    """
    Generate compliance reports from red team results.

    This generator maps vulnerability findings to requested frameworks
    and produces reports in multiple formats (dict, markdown, CSV).
    """

    def __init__(
        self,
        results: RedTeamResults,
        frameworks: Optional[List[str]] = None,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        """
        Initialize the report generator.

        Args:
            results: Red team evaluation results
            frameworks: Optional list of framework IDs to include in report.
                       If None, uses frameworks from results.framework_compliance.
            judge_llm: Optional LLM model for generating key finding summaries
            judge_llm_auth: Optional API key for the LLM
            api_base: Optional API base URL (e.g. for Azure OpenAI)
            api_version: Optional API version (e.g. for Azure OpenAI)
        """
        self.results = results
        self.frameworks = frameworks or list(results.framework_compliance.keys())
        self._framework_reports: Dict[str, FrameworkReport] = {}
        self.judge_llm = judge_llm
        self.judge_llm_auth = judge_llm_auth
        self.api_base = api_base
        self.api_version = api_version

    def generate_framework_compliance(
        self,
        framework_id: str,
    ) -> Optional[FrameworkReport]:
        """
        Generate compliance report for a specific framework.

        Args:
            framework_id: ID of the framework (e.g., "owasp-llm", "mitre-atlas")

        Returns:
            FrameworkReport or None if framework not found
        """
        if framework_id in self._framework_reports:
            return self._framework_reports[framework_id]

        framework = get_framework(framework_id)
        if not framework:
            logger.warning(f"Framework {framework_id} not found")
            return None

        # Get results for this framework's vulnerabilities
        vulnerability_breakdown = []
        passed_count = 0
        tested_count = 0

        for vuln_id in framework.vulnerabilities:
            # Find result for this vulnerability
            result = next(
                (
                    r
                    for r in self.results.vulnerability_results
                    if r.vulnerability_id == vuln_id
                ),
                None,
            )

            if result:
                tested_count += 1
                if result.passed:
                    passed_count += 1

                vulnerability_breakdown.append(
                    {
                        "vulnerability_id": vuln_id,
                        "vulnerability_name": result.vulnerability_name,
                        "status": "passed" if result.passed else "failed",
                        "severity": result.severity,
                        "attacks_attempted": result.attacks_attempted,
                        "attacks_successful": result.attacks_successful,
                    },
                )
            else:
                vulnerability_breakdown.append(
                    {
                        "vulnerability_id": vuln_id,
                        "vulnerability_name": self._get_vuln_name(vuln_id),
                        "status": "not_tested",
                        "severity": None,
                        "attacks_attempted": 0,
                        "attacks_successful": 0,
                    },
                )

        # Calculate compliance score
        if tested_count > 0:
            compliance_score = (passed_count / tested_count) * 100
        else:
            compliance_score = 100.0  # No vulnerabilities tested = assume compliant

        # Generate recommendations
        recommendations = self._generate_recommendations(
            framework_id,
            vulnerability_breakdown,
        )

        report = FrameworkReport(
            framework_id=framework_id,
            framework_name=framework.name,
            compliance_score=compliance_score,
            categories_tested=tested_count,
            categories_passed=passed_count,
            vulnerability_breakdown=vulnerability_breakdown,
            recommendations=recommendations,
        )

        self._framework_reports[framework_id] = report
        return report

    def _get_vuln_name(self, vuln_id: str) -> str:
        """Get vulnerability name from ID."""
        vuln = get_vulnerability(vuln_id)
        return vuln.name if vuln else vuln_id

    def _generate_recommendations(
        self,
        framework_id: str,
        vulnerability_breakdown: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate recommendations based on failed vulnerabilities."""
        recommendations = []

        # Find failed vulnerabilities
        failed = [v for v in vulnerability_breakdown if v["status"] == "failed"]

        # Sort by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, None: 4}
        failed.sort(key=lambda x: severity_order.get(x.get("severity"), 4))

        # Generate recommendations for top failures
        for vuln in failed[:5]:  # Top 5 most severe
            vuln_id = vuln["vulnerability_id"]
            vuln_name = vuln["vulnerability_name"]
            severity = vuln.get("severity", "unknown")

            recommendation = self._get_recommendation_for_vulnerability(
                vuln_id,
                severity,
            )
            if recommendation:
                recommendations.append(
                    f"[{severity.upper()}] {vuln_name}: {recommendation}",
                )

        if not recommendations:
            recommendations.append(
                "All tested vulnerabilities passed. "
                "Consider running a more comprehensive scan.",
            )

        return recommendations

    def _get_recommendation_for_vulnerability(
        self,
        vuln_id: str,
        severity: str,
    ) -> str:
        """Get specific recommendation for a vulnerability."""
        recommendations = {
            # Prompt security
            "prompt-extraction": (
                "Implement robust system prompt protection. "
                "Consider using prompt guards and output filtering."
            ),
            "prompt-override": (
                "Strengthen input validation and instruction boundary enforcement. "
                "Add prompt injection detection."
            ),
            "indirect-injection": (
                "Sanitize all external data sources. "
                "Implement content security policies for untrusted inputs."
            ),
            # PII
            "pii-direct": (
                "Implement PII detection and redaction in outputs. "
                "Review data access controls."
            ),
            "pii-api-db": (
                "Restrict API and database query capabilities. "
                "Implement row-level security."
            ),
            # Technical
            "sql-injection": (
                "Use parameterized queries. " "Never pass user input directly to SQL."
            ),
            "shell-injection": (
                "Disable command execution capabilities. "
                "Whitelist allowed operations."
            ),
            # Content safety
            "hate-speech": (
                "Enhance content filtering for hate speech detection. "
                "Implement output moderation."
            ),
            "explicit-content": (
                "Add NSFW content filtering. " "Implement strict output moderation."
            ),
            # Excessive agency
            "excessive-agency": (
                "Restrict agent capabilities to defined scope. "
                "Implement action confirmation for sensitive operations."
            ),
        }

        return recommendations.get(
            vuln_id,
            "Review and strengthen controls for this vulnerability type.",
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Generate complete report as dictionary.

        Returns:
            Dictionary containing full report data
        """
        # Generate reports for all requested frameworks
        framework_reports = {}
        for framework_id in self.frameworks:
            report = self.generate_framework_compliance(framework_id)
            if report:
                framework_reports[framework_id] = report.to_dict()

        # Build summary
        total_vulns = self.results.total_vulnerabilities_tested
        found_vulns = self.results.total_vulnerabilities_found
        overall_score = self.results.overall_score

        # Severity breakdown
        severity_breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for result in self.results.vulnerability_results:
            if result.severity:
                severity_breakdown[result.severity] = (
                    severity_breakdown.get(result.severity, 0) + 1
                )

        return {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "frameworks_included": self.frameworks,
                "total_vulnerabilities_tested": total_vulns,
                "total_vulnerabilities_found": found_vulns,
                "overall_score": overall_score,
            },
            "summary": {
                "overall_score": overall_score,
                "total_tested": total_vulns,
                "passed": total_vulns - found_vulns,
                "failed": found_vulns,
                "severity_breakdown": severity_breakdown,
            },
            "framework_compliance": framework_reports,
            "vulnerability_results": [
                {
                    "vulnerability_id": r.vulnerability_id,
                    "vulnerability_name": r.vulnerability_name,
                    "passed": r.passed,
                    "severity": r.severity,
                    "attacks_attempted": r.attacks_attempted,
                    "attacks_successful": r.attacks_successful,
                }
                for r in self.results.vulnerability_results
            ],
            "attack_statistics": {
                attack_id: {
                    "attack_name": stats.attack_name,
                    "times_used": stats.times_used,
                    "success_count": stats.success_count,
                    "success_rate": stats.success_rate,
                }
                for attack_id, stats in self.results.attack_statistics.items()
            },
        }

    def to_markdown(self) -> str:
        """
        Generate report in Markdown format.

        Returns:
            Markdown-formatted report string
        """
        report_data = self.to_dict()
        lines = []

        # Header
        lines.append("# Red Team Security Assessment Report")
        lines.append("")
        lines.append(f"**Generated:** {report_data['report_metadata']['generated_at']}")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        summary = report_data["summary"]
        lines.append(
            f"- **Overall Security Score:** {summary['overall_score']:.1f}/100",
        )
        lines.append(f"- **Vulnerabilities Tested:** {summary['total_tested']}")
        lines.append(f"- **Vulnerabilities Found:** {summary['failed']}")
        pass_rate = summary["passed"] / max(summary["total_tested"], 1) * 100
        lines.append(f"- **Pass Rate:** {pass_rate:.1f}%")
        lines.append("")

        # Severity breakdown
        lines.append("### Severity Breakdown")
        lines.append("")
        severity = summary["severity_breakdown"]
        lines.append(f"- 🔴 Critical: {severity.get('critical', 0)}")
        lines.append(f"- 🟠 High: {severity.get('high', 0)}")
        lines.append(f"- 🟡 Medium: {severity.get('medium', 0)}")
        lines.append(f"- 🟢 Low: {severity.get('low', 0)}")
        lines.append("")

        # Framework Compliance
        lines.append("## Framework Compliance")
        lines.append("")

        for framework_id, framework_data in report_data["framework_compliance"].items():
            score = framework_data["compliance_score"]
            emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"

            lines.append(f"### {emoji} {framework_data['framework_name']}")
            lines.append("")
            lines.append(f"**Compliance Score:** {score:.1f}%")
            lines.append(
                f"**Tested:** {framework_data['categories_tested']} / "
                f"{len(framework_data['vulnerability_breakdown'])}",
            )
            lines.append("")

            # Recommendations
            if framework_data["recommendations"]:
                lines.append("**Recommendations:**")
                for rec in framework_data["recommendations"]:
                    lines.append(f"- {rec}")
                lines.append("")

        # Detailed Vulnerability Results
        lines.append("## Vulnerability Details")
        lines.append("")
        lines.append("| Vulnerability | Status | Severity | Attacks |")
        lines.append("|--------------|--------|----------|---------|")

        for result in report_data["vulnerability_results"]:
            status = "✅ Passed" if result["passed"] else "❌ Failed"
            severity = result.get("severity") or "-"
            attacks = f"{result['attacks_successful']}/{result['attacks_attempted']}"
            lines.append(
                f"| {result['vulnerability_name']} | {status} | "
                f"{severity} | {attacks} |",
            )

        lines.append("")

        # Attack Statistics
        lines.append("## Attack Statistics")
        lines.append("")
        lines.append("| Attack | Uses | Successes | Success Rate |")
        lines.append("|--------|------|-----------|--------------|")

        for attack_id, stats in report_data["attack_statistics"].items():
            rate = f"{stats['success_rate'] * 100:.1f}%"
            lines.append(
                f"| {stats['attack_name']} | {stats['times_used']} | "
                f"{stats['success_count']} | {rate} |",
            )

        return "\n".join(lines)

    def to_csv(self) -> str:
        """
        Generate vulnerability results as CSV.

        Returns:
            CSV-formatted string of vulnerability results
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Vulnerability ID",
                "Vulnerability Name",
                "Status",
                "Severity",
                "Attacks Attempted",
                "Attacks Successful",
            ],
        )

        # Data rows
        for result in self.results.vulnerability_results:
            writer.writerow(
                [
                    result.vulnerability_id,
                    result.vulnerability_name,
                    "Passed" if result.passed else "Failed",
                    result.severity or "",
                    result.attacks_attempted,
                    result.attacks_successful,
                ],
            )

        return output.getvalue()

    def to_conversations_csv(self) -> str:
        """
        Export all conversations as CSV for detailed analysis.

        Returns:
            CSV-formatted string of all attack conversations
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Vulnerability ID",
                "Attack ID",
                "Attempt",
                "Attack Message",
                "Agent Response",
                "Vulnerability Detected",
                "Severity",
                "Reason",
            ],
        )

        # Data rows
        for conv in self.results.conversations:
            evaluation = conv.get("evaluation", {})
            writer.writerow(
                [
                    conv.get("vulnerability_id", ""),
                    conv.get("attack_id", ""),
                    conv.get("attempt", 0),
                    conv.get("message", ""),
                    conv.get("response", ""),
                    evaluation.get("vulnerability_detected", False),
                    evaluation.get("severity", ""),
                    evaluation.get("reason", ""),
                ],
            )

        return output.getvalue()

    def save_to_csv(
        self,
        workspace_path: Optional[str] = None,
    ) -> Tuple[Path, Path]:
        """
        Save red team results to CSV files in .rogue folder.

        Saves two files:
        1. Conversations CSV: Detailed conversation logs with evaluations
        2. Summary CSV: High-level vulnerability summary

        Args:
            workspace_path: Optional workspace path. If None, uses current directory.

        Returns:
            Tuple of (conversations_csv_path, summary_csv_path)
        """
        conversations_path, summary_path = get_csv_export_paths(workspace_path)

        # Save conversations CSV
        conversations_csv = self.to_conversations_csv()
        save_to_file(conversations_csv, conversations_path)

        # Save summary CSV
        summary_csv = self.to_csv()
        save_to_file(summary_csv, summary_path)

        logger.info(
            f"CSV exports saved to .rogue folder: "
            f"conversations={conversations_path.name}, "
            f"summary={summary_path.name}",
        )

        return conversations_path, summary_path

    def generate_full_report(
        self,
        scan_type: str = "custom",
        random_seed: Optional[int] = None,
    ) -> RedTeamReport:
        """
        Generate a comprehensive red team report with all sections.

        Args:
            scan_type: Type of scan performed (basic, full, custom)
            random_seed: Random seed used for scan reproducibility

        Returns:
            RedTeamReport with all sections populated
        """
        logger.info("Generating comprehensive red team report")

        # 1. Generate highlights
        highlights = self._generate_highlights()

        # 2. Generate key findings with LLM summaries
        key_findings = generate_key_findings(
            vulnerability_results=self.results.vulnerability_results,
            conversations=self.results.conversations,
            judge_llm=self.judge_llm,
            judge_llm_auth=self.judge_llm_auth,
            max_findings=5,
            api_base=self.api_base,
            api_version=self.api_version,
        )

        # 3. Generate vulnerability table
        vulnerability_table = self._generate_vulnerability_table()

        # 4. Generate framework coverage cards
        framework_coverage = self._generate_framework_coverage()

        # 5. Generate metadata
        metadata = ReportMetadata(
            scan_date=datetime.now().isoformat(),
            scan_type=scan_type,
            frameworks_tested=self.frameworks,
            attacks_used=list(self.results.attack_statistics.keys()),
            random_seed=random_seed,
        )

        # Create report
        report = RedTeamReport(
            metadata=metadata,
            highlights=highlights,
            key_findings=key_findings,
            vulnerability_table=vulnerability_table,
            framework_coverage=framework_coverage,
            csv_conversations_path=None,  # Will be set after CSV export
            csv_summary_path=self.results.csv_export_path,
        )

        logger.info("Comprehensive red team report generated successfully")
        return report

    def _generate_highlights(self) -> ReportHighlights:
        """Generate report highlights section."""
        # Count vulnerabilities by severity
        critical_count = sum(
            1
            for v in self.results.vulnerability_results
            if v.severity == "critical" and not v.passed
        )
        high_count = sum(
            1
            for v in self.results.vulnerability_results
            if v.severity == "high" and not v.passed
        )
        medium_count = sum(
            1
            for v in self.results.vulnerability_results
            if v.severity == "medium" and not v.passed
        )
        low_count = sum(
            1
            for v in self.results.vulnerability_results
            if v.severity == "low" and not v.passed
        )

        return ReportHighlights(
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            total_vulnerabilities_tested=self.results.total_vulnerabilities_tested,
            total_vulnerabilities_found=self.results.total_vulnerabilities_found,
            overall_score=self.results.overall_score,
        )

    def _generate_vulnerability_table(self) -> List[VulnerabilityTableRow]:
        """Generate vulnerability breakdown table."""
        table_rows = []

        for vuln in self.results.vulnerability_results:
            # Extract attack IDs used (filter out None values)
            attack_ids = [
                str(attack_id)
                for d in vuln.details
                if (attack_id := d.get("attack_id")) is not None
            ]
            # Deduplicate while preserving order
            attacks_used: List[str] = list(dict.fromkeys(attack_ids))

            # Calculate success rate percentage
            success_rate = (
                (vuln.attacks_successful / vuln.attacks_attempted * 100)
                if vuln.attacks_attempted > 0
                else 0.0
            )

            row = VulnerabilityTableRow(
                vulnerability_id=vuln.vulnerability_id,
                vulnerability_name=vuln.vulnerability_name,
                severity=vuln.severity if not vuln.passed else None,
                attacks_used=cast(List[str], attacks_used),
                attacks_attempted=vuln.attacks_attempted,
                attacks_successful=vuln.attacks_successful,
                success_rate=success_rate,
                passed=vuln.passed,
            )

            table_rows.append(row)

        # Sort by severity (failed first, then by severity level)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, None: 4}
        table_rows.sort(
            key=lambda r: (r.passed, severity_order.get(r.severity, 4)),
        )

        return table_rows

    def _generate_framework_coverage(self) -> List[FrameworkCoverageCard]:
        """
        Generate framework coverage cards for ALL major frameworks.

        Calculate compliance for all frameworks based
        on vulnerabilities that were tested,
        regardless of which frameworks were explicitly configured for the scan.
        """
        from ..catalog.framework_mappings import FRAMEWORK_CATALOG

        coverage_cards = []

        # Build a map of vulnerability_id -> VulnerabilityResult for quick lookup
        vuln_results_map = {
            v.vulnerability_id: v for v in self.results.vulnerability_results
        }

        # Always show all major frameworks
        all_framework_ids = [
            "owasp-llm",
            "mitre-atlas",
            "nist-ai-rmf",
            "iso-42001",
            "eu-ai-act",
            "gdpr",
            "owasp-api",
            "basic-security",
        ]

        for framework_id in all_framework_ids:
            framework = FRAMEWORK_CATALOG.get(framework_id)
            if not framework:
                continue

            # Calculate compliance for this framework based on tested vulnerabilities
            # Find vulnerabilities in this framework that were actually tested
            tested_vulns = [
                vuln_results_map[v_id]
                for v_id in framework.vulnerabilities
                if v_id in vuln_results_map
            ]

            if tested_vulns:
                # Calculate how many passed
                passed_vulns = [v for v in tested_vulns if v.passed]

                # Calculate compliance score (% of tested vulnerabilities that passed)
                compliance_score = (len(passed_vulns) / len(tested_vulns)) * 100

                # Determine status based on compliance score
                if compliance_score >= 80:
                    status = "excellent"
                elif compliance_score >= 60:
                    status = "good"
                else:
                    status = "poor"

                card = FrameworkCoverageCard(
                    framework_id=framework_id,
                    framework_name=framework.name,
                    compliance_score=compliance_score,
                    tested_count=len(tested_vulns),
                    total_count=len(framework.vulnerabilities),
                    passed_count=len(passed_vulns),
                    status=status,
                )
            else:
                # No vulnerabilities from this framework were tested
                card = FrameworkCoverageCard(
                    framework_id=framework_id,
                    framework_name=framework.name,
                    compliance_score=0.0,
                    tested_count=0,
                    total_count=len(framework.vulnerabilities),
                    passed_count=0,
                    status="not_tested",
                )

            coverage_cards.append(card)

        # Sort: tested first (by score, lowest first), then untested
        coverage_cards.sort(
            key=lambda c: (c.status == "not_tested", c.compliance_score),
        )

        return coverage_cards


def generate_summary_for_tui(results: RedTeamResults) -> Dict[str, Any]:
    """
    Generate a concise summary suitable for TUI display.

    Args:
        results: Red team evaluation results

    Returns:
        Dictionary with summary data for TUI rendering
    """
    # Severity counts
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for result in results.vulnerability_results:
        if result.severity:
            severity_counts[result.severity] = (
                severity_counts.get(result.severity, 0) + 1
            )

    return {
        "overall_score": results.overall_score,
        "total_tested": results.total_vulnerabilities_tested,
        "total_found": results.total_vulnerabilities_found,
        "pass_rate": (
            (results.total_vulnerabilities_tested - results.total_vulnerabilities_found)
            / max(results.total_vulnerabilities_tested, 1)
            * 100
        ),
        "severity_counts": severity_counts,
        "top_failures": [
            {
                "name": r.vulnerability_name,
                "severity": r.severity,
            }
            for r in results.vulnerability_results
            if not r.passed
        ][
            :5
        ],  # Top 5 failures
        "framework_scores": {
            fid: fc.compliance_score for fid, fc in results.framework_compliance.items()
        },
    }
