"""Unit tests for resilience report generation."""

from pathlib import Path

import pytest

from rogue.injectors.base_injector import InjectorId
from rogue.resilience.orchestrator import ResilienceOrchestrator
from rogue.server.resilience.report.generator import ResilienceReportGenerator
from rogue.server.resilience.report.web_formatter import format_for_web

FIXTURE_AGENT = Path(__file__).parent / "fixtures" / "resilience_test_agent.py"


async def _sample_results():
    orchestrator = ResilienceOrchestrator(
        injectors=[InjectorId.POLICY_VIOLATION, InjectorId.TOOL_MISUSE],
        python_entrypoint_file=str(FIXTURE_AGENT),
        business_context="Test store",
        experiments_per_injector=1,
        use_heuristics=True,
    )
    return await orchestrator.run_experiments()


@pytest.mark.asyncio
async def test_report_generator_produces_scorecard() -> None:
    sample_results = await _sample_results()
    generator = ResilienceReportGenerator(
        results=sample_results,
        injectors=["policy_violation", "tool_misuse"],
        architecture="single_agent",
    )
    report = generator.generate_full_report()
    assert report.highlights.total_experiments == 2
    assert len(report.experiment_table) == 2
    assert report.markdown_report.startswith("# Rogue Resilience Report")
    assert "Detection rate" in report.markdown_report


@pytest.mark.asyncio
async def test_report_csv_export() -> None:
    sample_results = await _sample_results()
    generator = ResilienceReportGenerator(results=sample_results)
    csv_text = generator.generate_csv_summary()
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("experiment_id,")
    assert len(lines) == 3  # header + 2 experiments


@pytest.mark.asyncio
async def test_web_formatter_structure() -> None:
    sample_results = await _sample_results()
    generator = ResilienceReportGenerator(results=sample_results)
    report = generator.generate_full_report()
    web = format_for_web(report)
    assert "highlights" in web
    assert "metrics_radar" in web
    assert len(web["metrics_radar"]) >= 3
    assert "timeline" in web
    assert isinstance(web["experiment_table"], list)


@pytest.mark.asyncio
async def test_report_from_results_dict() -> None:
    sample_results = await _sample_results()
    data = sample_results.model_dump()
    generator = ResilienceReportGenerator.from_results_dict(
        data,
        injectors=["policy_violation"],
        architecture="single_agent",
    )
    report = generator.generate_full_report()
    assert report.highlights.overall_score >= 0
