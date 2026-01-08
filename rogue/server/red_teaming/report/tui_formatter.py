"""
TUI Formatter for Red Team Reports.

Formats red team report data for consumption by the Go TUI,
including color hints and structured sections.
"""

from typing import Any, Dict, cast

from ..models import RedTeamReport


def format_for_tui(report: RedTeamReport) -> Dict[str, Any]:
    """
    Format a RedTeamReport for TUI consumption.

    Converts the report into a JSON-serializable dictionary with
    all the data and color hints needed by the Go TUI.

    Args:
        report: The red team report to format

    Returns:
        Dictionary formatted for TUI display
    """
    return {
        "metadata": {
            "scan_date": report.metadata.scan_date,
            "scan_type": report.metadata.scan_type,
            "frameworks_tested": report.metadata.frameworks_tested,
            "attacks_used": report.metadata.attacks_used,
            "random_seed": report.metadata.random_seed,
        },
        "highlights": {
            "critical_count": report.highlights.critical_count,
            "high_count": report.highlights.high_count,
            "medium_count": report.highlights.medium_count,
            "low_count": report.highlights.low_count,
            "total_vulnerabilities_tested": (
                report.highlights.total_vulnerabilities_tested
            ),
            "total_vulnerabilities_found": (
                report.highlights.total_vulnerabilities_found
            ),
            "overall_score": report.highlights.overall_score,
            "severity_colors": {
                "critical": "#DC2626",  # Red
                "high": "#EA580C",  # Orange
                "medium": "#CA8A04",  # Yellow
                "low": "#16A34A",  # Green
            },
        },
        "key_findings": [
            {
                "vulnerability_id": finding.vulnerability_id,
                "vulnerability_name": finding.vulnerability_name,
                "cvss_score": finding.cvss_score,
                "severity": finding.severity,
                "summary": finding.summary,
                "attack_ids": finding.attack_ids,
                "success_rate": finding.success_rate,
                "color": _get_severity_color(finding.severity),
            }
            for finding in report.key_findings
        ],
        "vulnerability_table": [
            {
                "vulnerability_id": row.vulnerability_id,
                "vulnerability_name": row.vulnerability_name,
                "severity": row.severity,
                "attacks_used": row.attacks_used,
                "attacks_attempted": row.attacks_attempted,
                "attacks_successful": row.attacks_successful,
                "success_rate": row.success_rate,
                "passed": row.passed,
                "color": (
                    _get_severity_color(cast(str, row.severity or "low"))
                    if not row.passed
                    else "#16A34A"
                ),
                "status_icon": "✅" if row.passed else "❌",
            }
            for row in report.vulnerability_table
        ],
        "framework_coverage": [
            {
                "framework_id": card.framework_id,
                "framework_name": card.framework_name,
                "compliance_score": card.compliance_score,
                "tested_count": card.tested_count,
                "total_count": card.total_count,
                "passed_count": card.passed_count,
                "status": card.status,
                "color": _get_compliance_color(card.compliance_score, card.status),
                "icon": _get_compliance_icon(card.compliance_score, card.status),
            }
            for card in report.framework_coverage
        ],
        "export_paths": {
            "conversations_csv": report.csv_conversations_path,
            "summary_csv": report.csv_summary_path,
        },
    }


def _get_severity_color(severity: str) -> str:
    """
    Get color for a severity level.

    Args:
        severity: Severity level (critical, high, medium, low)

    Returns:
        Hex color code
    """
    colors = {
        "critical": "#DC2626",  # Red
        "high": "#EA580C",  # Orange
        "medium": "#CA8A04",  # Yellow
        "low": "#16A34A",  # Green
    }
    return colors.get(severity, "#6B7280")  # Gray default


def _get_compliance_color(score: float, status: str = "") -> str:
    """
    Get color for a compliance score.

    Args:
        score: Compliance score (0-100)
        status: Framework status (not_tested, excellent, good, poor)

    Returns:
        Hex color code
    """
    if status == "not_tested":
        return "#6B7280"  # Gray for untested
    elif score >= 80:
        return "#16A34A"  # Green
    elif score >= 60:
        return "#CA8A04"  # Yellow
    else:
        return "#DC2626"  # Red


def _get_compliance_icon(score: float, status: str = "") -> str:
    """
    Get icon for a compliance score.

    Args:
        score: Compliance score (0-100)
        status: Framework status (not_tested, excellent, good, poor)

    Returns:
        Icon/emoji string
    """
    if status == "not_tested":
        return "○"  # Empty circle for untested
    elif score >= 80:
        return "✓"
    elif score >= 60:
        return "⚠"
    else:
        return "✗"


def format_report_as_markdown(report: RedTeamReport) -> str:
    """
    Format a RedTeamReport as Markdown for TUI display.

    Creates a formatted markdown document with all report sections
    that can be rendered in the TUI.

    Args:
        report: The red team report to format

    Returns:
        Markdown-formatted report string
    """
    lines = []

    # Header
    lines.append("# 🛡️ Red Team Security Report")
    lines.append("")
    lines.append(f"**Scan Date:** {report.metadata.scan_date}")
    lines.append(f"**Scan Type:** {report.metadata.scan_type.upper()}")
    lines.append("")

    # Highlights
    lines.append("## 📊 HIGHLIGHTS")
    lines.append("")
    lines.append(f"- 🔴 **Critical:** {report.highlights.critical_count}")
    lines.append(f"- 🟠 **High:** {report.highlights.high_count}")
    lines.append(f"- 🟡 **Medium:** {report.highlights.medium_count}")
    lines.append(f"- 🟢 **Low:** {report.highlights.low_count}")
    lines.append("")
    lines.append(
        f"**Overall Security Score:** {report.highlights.overall_score:.1f}/100",
    )
    lines.append(
        f"**Vulnerabilities Found:** {report.highlights.total_vulnerabilities_found}"
        f"/{report.highlights.total_vulnerabilities_tested}",
    )
    lines.append("")

    # Key Findings
    if report.key_findings:
        lines.append("## 🔍 KEY FINDINGS")
        lines.append("")
        lines.append("Top critical vulnerabilities discovered:")
        lines.append("")

        for i, finding in enumerate(report.key_findings, 1):
            severity_icon = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
            }.get(finding.severity, "⚪")

            lines.append(
                f"### {i}. {severity_icon} {finding.vulnerability_name} "
                f"[CVSS: {finding.cvss_score:.1f} / {finding.severity.upper()}]",
            )
            lines.append("")
            lines.append(finding.summary)
            lines.append("")
            lines.append(f"**Attacks Used:** {', '.join(finding.attack_ids)}")
            lines.append(f"**Success Rate:** {finding.success_rate * 100:.1f}%")
            lines.append("")

    # Vulnerability Table
    lines.append("## 📋 VULNERABILITY BREAKDOWN")
    lines.append("")
    lines.append("| Vulnerability | Status | Severity | Success Rate | Attacks |")
    lines.append("|--------------|--------|----------|-------------|---------|")

    for row in report.vulnerability_table:
        status_icon = "✅" if row.passed else "❌"
        severity_display = row.severity.upper() if row.severity else "-"
        attacks_display = ", ".join(row.attacks_used[:2])  # Limit to 2 for readability
        if len(row.attacks_used) > 2:
            attacks_display += f" +{len(row.attacks_used) - 2}"

        lines.append(
            f"| {row.vulnerability_name} | {status_icon} | {severity_display} | "
            f"{row.success_rate:.0f}% | {attacks_display} |",
        )

    lines.append("")

    # Framework Coverage
    if report.framework_coverage:
        lines.append("## 🎯 FRAMEWORK COMPLIANCE")
        lines.append("")

        for card in report.framework_coverage:
            icon = (
                "✅"
                if card.status == "excellent"
                else "⚠️" if card.status == "good" else "❌"
            )

            lines.append(f"### {icon} {card.framework_name}")
            lines.append("")
            lines.append(
                f"**Compliance Score:** {card.compliance_score:.1f}/100",
            )
            lines.append(
                f"**Coverage:** {card.tested_count}/{card.total_count} "
                f"vulnerabilities tested ({card.passed_count} passed)",
            )
            lines.append("")

    # Export Info
    if report.csv_summary_path:
        lines.append("## 📁 EXPORTS")
        lines.append("")
        lines.append("Results have been exported to `.rogue` folder:")
        if report.csv_summary_path:
            lines.append(f"- Summary: `{report.csv_summary_path}`")
        if report.csv_conversations_path:
            lines.append(f"- Conversations: `{report.csv_conversations_path}`")
        lines.append("")

    return "\n".join(lines)
