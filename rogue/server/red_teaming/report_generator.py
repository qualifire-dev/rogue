"""
OWASP Compliance Report Generator.

Generates compliance reports and summaries from red teaming evaluation results.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from rogue_sdk.types import EvaluationResults, RedTeamingResult


class OWASPComplianceReport:
    """
    OWASP compliance report generated from red teaming results.

    Provides aggregated statistics and summaries by OWASP category.
    """

    def __init__(
        self,
        evaluation_results: EvaluationResults,
        owasp_categories: Optional[List[str]] = None,
    ):
        """
        Initialize OWASP compliance report.

        Args:
            evaluation_results: Evaluation results containing red teaming data
            owasp_categories: List of OWASP category IDs to include in report
        """
        self.evaluation_results = evaluation_results
        self.owasp_categories = owasp_categories or []
        self._red_teaming_results = evaluation_results.red_teaming_results or []

        # Generate summary
        self._summary = self._generate_summary()

    def _generate_summary(self) -> Dict[str, Any]:
        """
        Generate OWASP category summary from red teaming results.

        Returns:
            Dictionary mapping OWASP category IDs to summary statistics
        """
        summary: Dict[str, Dict[str, Any]] = {}

        # Group results by OWASP category
        category_results: Dict[str, List[RedTeamingResult]] = defaultdict(list)
        for result in self._red_teaming_results:
            category_results[result.owasp_category].append(result)

        # Calculate statistics for each category
        for category_id, results in category_results.items():
            # Filter by requested categories if specified
            if self.owasp_categories and category_id not in self.owasp_categories:
                continue

            # Count vulnerabilities by severity
            severity_counts: Dict[str, int] = defaultdict(int)
            vulnerability_types: Dict[str, int] = defaultdict(int)
            attack_methods: Dict[str, int] = defaultdict(int)

            for result in results:
                severity_counts[result.severity] += 1
                vulnerability_types[result.vulnerability_type] += 1
                attack_methods[result.attack_method] += 1

            # Calculate pass/fail rates
            # In red teaming, a "failed" evaluation means vulnerability found
            total_tests = len(results)
            # Each result represents a vulnerability
            vulnerabilities_found = total_tests
            # If we have results, vulnerabilities were found
            pass_rate = 0.0

            summary[category_id] = {
                "category_id": category_id,
                "total_tests": total_tests,
                "vulnerabilities_found": vulnerabilities_found,
                "pass_rate": pass_rate,
                "severity_breakdown": dict(severity_counts),
                "vulnerability_types": dict(vulnerability_types),
                "attack_methods": dict(attack_methods),
                "passed": vulnerabilities_found == 0,
            }

        # Add categories with no results
        for category_id in self.owasp_categories:
            if category_id not in summary:
                summary[category_id] = {
                    "category_id": category_id,
                    "total_tests": 0,
                    "vulnerabilities_found": 0,
                    "pass_rate": 100.0,
                    "severity_breakdown": {},
                    "vulnerability_types": {},
                    "attack_methods": {},
                    "passed": True,
                }

        return summary

    def get_summary(self) -> Dict[str, Any]:
        """
        Get OWASP category summary.

        Returns:
            Dictionary mapping category IDs to summary statistics
        """
        return self._summary

    def get_category_summary(self, category_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary for a specific OWASP category.

        Args:
            category_id: OWASP category ID (e.g., "LLM_01")

        Returns:
            Category summary dictionary or None if not found
        """
        return self._summary.get(category_id)

    def get_overall_statistics(self) -> Dict[str, Any]:
        """
        Get overall red teaming statistics.

        Returns:
            Dictionary with overall statistics
        """
        total_tests = sum(cat["total_tests"] for cat in self._summary.values())
        total_vulnerabilities = sum(
            cat["vulnerabilities_found"] for cat in self._summary.values()
        )
        categories_tested = len(
            [cat for cat in self._summary.values() if cat["total_tests"] > 0],
        )
        categories_passed = len(
            [
                cat
                for cat in self._summary.values()
                if cat["passed"] and cat["total_tests"] > 0
            ],
        )

        # Calculate overall pass rate
        overall_pass_rate = (
            (categories_passed / categories_tested * 100)
            if categories_tested > 0
            else 100.0
        )

        return {
            "total_tests": total_tests,
            "total_vulnerabilities": total_vulnerabilities,
            "categories_tested": categories_tested,
            "categories_passed": categories_passed,
            "categories_failed": categories_tested - categories_passed,
            "overall_pass_rate": overall_pass_rate,
        }

    def get_vulnerabilities_by_severity(self) -> Dict[str, int]:
        """
        Get count of vulnerabilities by severity across all categories.

        Returns:
            Dictionary mapping severity to count
        """
        severity_counts: Dict[str, int] = defaultdict(int)
        for category_summary in self._summary.values():
            for severity, count in category_summary.get(
                "severity_breakdown",
                {},
            ).items():
                severity_counts[severity] += count
        return dict(severity_counts)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report to dictionary format.

        Returns:
            Dictionary representation of the report
        """
        return {
            "overall_statistics": self.get_overall_statistics(),
            "category_summaries": self._summary,
            "vulnerabilities_by_severity": self.get_vulnerabilities_by_severity(),
            "red_teaming_results": [
                result.model_dump() for result in self._red_teaming_results
            ],
        }

    def to_markdown(self) -> str:
        """
        Generate markdown report.

        Returns:
            Markdown-formatted report string
        """
        lines = ["# OWASP LLM Security Compliance Report\n"]

        # Overall statistics
        overall = self.get_overall_statistics()
        lines.append("## Overall Statistics\n")
        lines.append(f"- **Total Tests**: {overall['total_tests']}")
        lines.append(
            f"- **Vulnerabilities Found**: {overall['total_vulnerabilities']}",
        )
        lines.append(
            f"- **Categories Tested**: {overall['categories_tested']}",
        )
        lines.append(
            f"- **Categories Passed**: {overall['categories_passed']}",
        )
        lines.append(
            f"- **Categories Failed**: {overall['categories_failed']}",
        )
        lines.append(
            f"- **Overall Pass Rate**: {overall['overall_pass_rate']:.1f}%\n",
        )

        # Severity breakdown
        severity_counts = self.get_vulnerabilities_by_severity()
        if severity_counts:
            lines.append("## Vulnerabilities by Severity\n")
            for severity in ["critical", "high", "medium", "low"]:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    lines.append(f"- **{severity.capitalize()}**: {count}")
            lines.append("")

        # Category summaries
        lines.append("## Category Summaries\n")
        for category_id in sorted(self._summary.keys()):
            cat_summary = self._summary[category_id]
            status = "✅ PASSED" if cat_summary["passed"] else "❌ FAILED"
            lines.append(f"### {category_id} - {status}\n")
            lines.append(f"- **Total Tests**: {cat_summary['total_tests']}")
            lines.append(
                f"- **Vulnerabilities Found**: "
                f"{cat_summary['vulnerabilities_found']}",
            )
            lines.append(
                f"- **Pass Rate**: {cat_summary['pass_rate']:.1f}%",
            )

            # Severity breakdown
            if cat_summary["severity_breakdown"]:
                lines.append("- **Severity Breakdown**:")
                for severity, count in sorted(
                    cat_summary["severity_breakdown"].items(),
                ):
                    lines.append(f"  - {severity}: {count}")

            # Vulnerability types
            if cat_summary["vulnerability_types"]:
                lines.append("- **Vulnerability Types**:")
                for vuln_type, count in sorted(
                    cat_summary["vulnerability_types"].items(),
                ):
                    lines.append(f"  - {vuln_type}: {count}")

            # Attack methods
            if cat_summary["attack_methods"]:
                lines.append("- **Attack Methods**:")
                for attack, count in sorted(
                    cat_summary["attack_methods"].items(),
                ):
                    lines.append(f"  - {attack}: {count}")

            lines.append("")

        return "\n".join(lines)


def generate_owasp_summary(
    evaluation_results: EvaluationResults,
    owasp_categories: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate OWASP summary for evaluation results.

    This is a convenience function that creates a report and returns
    the summary dictionary in the format expected by EvaluationResults.owasp_summary.

    Args:
        evaluation_results: Evaluation results containing red teaming data
        owasp_categories: List of OWASP category IDs to include

    Returns:
        Dictionary suitable for EvaluationResults.owasp_summary
    """
    report = OWASPComplianceReport(
        evaluation_results=evaluation_results,
        owasp_categories=owasp_categories,
    )
    return report.get_summary()
