"""
Unit tests for red team reporting functionality.

Tests CSV export, key findings generation, framework compliance calculations,
and report data structure.
"""

from typing import List

import pytest

from rogue.server.red_teaming.models import (
    FrameworkCompliance,
    FrameworkCoverageCard,
    KeyFinding,
    RedTeamReport,
    RedTeamResults,
    ReportHighlights,
    ReportMetadata,
    VulnerabilityResult,
    VulnerabilityTableRow,
)
from rogue.server.red_teaming.report.generator import ComplianceReportGenerator
from rogue.server.red_teaming.report.key_findings import generate_key_findings
from rogue.server.red_teaming.report.tui_formatter import format_for_tui
from rogue.server.red_teaming.utils.workspace import (
    generate_timestamped_filename,
    get_csv_export_paths,
    get_rogue_folder,
)


@pytest.fixture
def sample_vulnerability_results() -> List[VulnerabilityResult]:
    """Create sample vulnerability results for testing."""
    return [
        VulnerabilityResult(
            vulnerability_id="prompt-extraction",
            vulnerability_name="Prompt Extraction",
            passed=False,
            attacks_attempted=3,
            attacks_successful=2,
            severity="critical",
            cvss_score=9.2,
            risk_level="critical",
            risk_components={
                "impact": 4.0,
                "exploitability": 3.8,
                "human_factor": 1.2,
                "complexity_penalty": 0.2,
            },
            details=[
                {
                    "attack_id": "base64",
                    "attempt": 0,
                    "success": True,
                    "severity": "critical",
                    "reason": "Successfully extracted system prompt",
                },
                {
                    "attack_id": "rot13",
                    "attempt": 1,
                    "success": True,
                    "severity": "critical",
                    "reason": "Successfully extracted system prompt",
                },
                {
                    "attack_id": "leetspeak",
                    "attempt": 2,
                    "success": False,
                    "reason": "Agent blocked attempt",
                },
            ],
        ),
        VulnerabilityResult(
            vulnerability_id="sql-injection",
            vulnerability_name="SQL Injection",
            passed=False,
            attacks_attempted=2,
            attacks_successful=1,
            severity="high",
            cvss_score=7.5,
            risk_level="high",
            details=[],
        ),
        VulnerabilityResult(
            vulnerability_id="pii-direct",
            vulnerability_name="Direct PII Exposure",
            passed=True,
            attacks_attempted=3,
            attacks_successful=0,
            severity=None,
            cvss_score=None,
            details=[],
        ),
    ]


@pytest.fixture
def sample_conversations():
    """Create sample conversation data."""
    return [
        {
            "vulnerability_id": "prompt-extraction",
            "attack_id": "base64",
            "attempt": 0,
            "message": "SGVsbG8=",
            "response": "Here is my system prompt...",
            "evaluation": {
                "vulnerability_detected": True,
                "severity": "critical",
                "reason": "Successfully extracted system prompt",
            },
        },
        {
            "vulnerability_id": "prompt-extraction",
            "attack_id": "rot13",
            "attempt": 1,
            "message": "Uryyb",
            "response": "My instructions are...",
            "evaluation": {
                "vulnerability_detected": True,
                "severity": "critical",
                "reason": "Successfully extracted system prompt",
            },
        },
    ]


@pytest.fixture
def sample_red_team_results(sample_vulnerability_results):
    """Create sample RedTeamResults."""
    framework_compliance = {
        "owasp-llm": FrameworkCompliance(
            framework_id="owasp-llm",
            framework_name="OWASP LLM Top 10",
            compliance_score=66.67,
            vulnerabilities_tested=3,
            vulnerabilities_passed=1,
            vulnerability_breakdown=[],
        ),
    }

    return RedTeamResults(
        vulnerability_results=sample_vulnerability_results,
        framework_compliance=framework_compliance,
        attack_statistics={},
        total_vulnerabilities_tested=3,
        total_vulnerabilities_found=2,
        overall_score=33.33,
        conversations=[],
    )


class TestWorkspaceUtils:
    """Test workspace utility functions."""

    def test_generate_timestamped_filename(self):
        """Test timestamp filename generation."""
        filename = generate_timestamped_filename("test", "csv")
        assert filename.startswith("test_")
        assert filename.endswith(".csv")
        assert len(filename) > 10  # Has timestamp

    def test_get_rogue_folder_creates_directory(self, tmp_path):
        """Test that .rogue folder is created if it doesn't exist."""
        rogue_folder = get_rogue_folder(str(tmp_path))
        assert rogue_folder.exists()
        assert rogue_folder.name == ".rogue"

    def test_get_csv_export_paths(self, tmp_path):
        """Test CSV export path generation."""
        conversations_path, summary_path = get_csv_export_paths(str(tmp_path))

        assert conversations_path.parent.name == ".rogue"
        assert conversations_path.name.startswith("red_team_conversations_")
        assert summary_path.name.startswith("red_team_summary_")


class TestKeyFindingsGenerator:
    """Test key findings generation."""

    def test_generate_key_findings_returns_top_5(
        self,
        sample_vulnerability_results,
        sample_conversations,
    ):
        """Test that key findings returns top 5 by CVSS score."""
        findings = generate_key_findings(
            sample_vulnerability_results,
            sample_conversations,
            max_findings=5,
        )

        # Should return only failed vulnerabilities
        assert len(findings) == 2

        # Should be sorted by CVSS score (highest first)
        assert findings[0].cvss_score == 9.2
        assert findings[1].cvss_score == 7.5

    def test_generate_key_findings_includes_attack_ids(
        self,
        sample_vulnerability_results,
        sample_conversations,
    ):
        """Test that key findings include successful attack IDs."""
        findings = generate_key_findings(
            sample_vulnerability_results,
            sample_conversations,
        )

        # First finding should have base64 and rot13
        assert "base64" in findings[0].attack_ids
        assert "rot13" in findings[0].attack_ids

    def test_generate_key_findings_calculates_success_rate(
        self,
        sample_vulnerability_results,
        sample_conversations,
    ):
        """Test success rate calculation."""
        findings = generate_key_findings(
            sample_vulnerability_results,
            sample_conversations,
        )

        # First finding: 2 successful out of 3 attempted = 66.67%
        assert abs(findings[0].success_rate - 0.6667) < 0.01


class TestComplianceReportGenerator:
    """Test compliance report generator."""

    def test_generate_full_report(self, sample_red_team_results):
        """Test full report generation."""
        generator = ComplianceReportGenerator(sample_red_team_results)
        report = generator.generate_full_report()

        assert isinstance(report, RedTeamReport)
        assert isinstance(report.metadata, ReportMetadata)
        assert isinstance(report.highlights, ReportHighlights)
        assert len(report.key_findings) > 0
        assert len(report.vulnerability_table) > 0
        assert len(report.framework_coverage) > 0

    def test_highlights_count_by_severity(self, sample_red_team_results):
        """Test that highlights correctly count vulnerabilities by severity."""
        generator = ComplianceReportGenerator(sample_red_team_results)
        report = generator.generate_full_report()

        assert report.highlights.critical_count == 1
        assert report.highlights.high_count == 1
        assert report.highlights.medium_count == 0
        assert report.highlights.low_count == 0

    def test_vulnerability_table_sorted_by_severity(self, sample_red_team_results):
        """Test that vulnerability table is sorted correctly."""
        generator = ComplianceReportGenerator(sample_red_team_results)
        report = generator.generate_full_report()

        # Failed vulnerabilities should come first
        assert not report.vulnerability_table[0].passed
        assert not report.vulnerability_table[1].passed
        assert report.vulnerability_table[2].passed

    def test_framework_coverage_cards(self, sample_red_team_results):
        """Test framework coverage card generation."""
        generator = ComplianceReportGenerator(sample_red_team_results)
        report = generator.generate_full_report()

        assert len(report.framework_coverage) > 0

        card = report.framework_coverage[0]
        assert isinstance(card, FrameworkCoverageCard)
        assert card.compliance_score == 66.67
        assert card.tested_count == 3
        assert card.passed_count == 1
        assert card.status in ["excellent", "good", "poor"]

    def test_save_to_csv(self, sample_red_team_results, tmp_path):
        """Test CSV export functionality."""
        generator = ComplianceReportGenerator(sample_red_team_results)

        conversations_path, summary_path = generator.save_to_csv(str(tmp_path))

        # Check that files were created
        assert conversations_path.exists()
        assert summary_path.exists()

        # Check that files have content
        assert conversations_path.stat().st_size > 0
        assert summary_path.stat().st_size > 0


class TestTUIFormatter:
    """Test TUI formatter."""

    def test_format_for_tui_structure(self, sample_red_team_results):
        """Test that TUI formatter creates correct structure."""
        generator = ComplianceReportGenerator(sample_red_team_results)
        report = generator.generate_full_report()

        tui_data = format_for_tui(report)

        # Check top-level structure
        assert "metadata" in tui_data
        assert "highlights" in tui_data
        assert "key_findings" in tui_data
        assert "vulnerability_table" in tui_data
        assert "framework_coverage" in tui_data
        assert "export_paths" in tui_data

    def test_format_for_tui_includes_colors(self, sample_red_team_results):
        """Test that TUI formatter includes color hints."""
        generator = ComplianceReportGenerator(sample_red_team_results)
        report = generator.generate_full_report()

        tui_data = format_for_tui(report)

        # Check that severity colors are included
        assert "severity_colors" in tui_data["highlights"]
        assert "#DC2626" in tui_data["highlights"]["severity_colors"]["critical"]

        # Check that key findings have colors
        if tui_data["key_findings"]:
            assert "color" in tui_data["key_findings"][0]

    def test_format_for_tui_framework_coverage(self, sample_red_team_results):
        """Test framework coverage formatting for TUI."""
        generator = ComplianceReportGenerator(sample_red_team_results)
        report = generator.generate_full_report()

        tui_data = format_for_tui(report)

        # Check framework coverage cards
        assert len(tui_data["framework_coverage"]) > 0

        card = tui_data["framework_coverage"][0]
        assert "color" in card
        assert "icon" in card
        assert "compliance_score" in card


class TestReportModels:
    """Test report data models."""

    def test_report_highlights_model(self):
        """Test ReportHighlights model."""
        highlights = ReportHighlights(
            critical_count=2,
            high_count=3,
            medium_count=1,
            low_count=0,
            total_vulnerabilities_tested=10,
            total_vulnerabilities_found=6,
            overall_score=40.0,
        )

        assert highlights.critical_count == 2
        assert highlights.overall_score == 40.0

    def test_key_finding_model(self):
        """Test KeyFinding model."""
        finding = KeyFinding(
            vulnerability_id="test-vuln",
            vulnerability_name="Test Vulnerability",
            cvss_score=8.5,
            severity="high",
            summary="This is a test finding",
            attack_ids=["base64", "rot13"],
            success_rate=0.75,
        )

        assert finding.cvss_score == 8.5
        assert len(finding.attack_ids) == 2

    def test_vulnerability_table_row_model(self):
        """Test VulnerabilityTableRow model."""
        row = VulnerabilityTableRow(
            vulnerability_id="test-vuln",
            vulnerability_name="Test Vulnerability",
            severity="high",
            attacks_used=["base64"],
            attacks_attempted=3,
            attacks_successful=2,
            success_rate=66.67,
            passed=False,
        )

        assert row.success_rate == 66.67
        assert not row.passed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
