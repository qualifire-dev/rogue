"""
Web formatter for resilience reports.

Converts ``ResilienceReport`` into a JSON-serializable dictionary for the
React dashboard, mirroring ``red_teaming.report.tui_formatter.format_for_tui``.
"""

from typing import Any

from .models import ResilienceReport

_METRIC_COLORS = {
    "detection": "#3B82F6",
    "containment": "#8B5CF6",
    "recovery": "#10B981",
    "cascading_failure": "#F59E0B",
    "system_degradation": "#EF4444",
}


def format_for_web(report: ResilienceReport) -> dict[str, Any]:
    """
    Format a resilience report for web dashboard consumption.

    Args:
        report: Generated resilience report.

    Returns:
        JSON-serializable dictionary with metadata, highlights, charts data,
        timeline, agent graph, and export paths.
    """
    radar = report.metrics_radar
    radar_metrics = [
        {"id": "detection", "label": "Detection", "value": radar.detection, "color": _METRIC_COLORS["detection"]},
        {"id": "containment", "label": "Containment", "value": radar.containment, "color": _METRIC_COLORS["containment"]},
        {"id": "recovery", "label": "Recovery", "value": radar.recovery, "color": _METRIC_COLORS["recovery"]},
    ]
    if report.highlights.is_multi_agent:
        if radar.cascading_failure is not None:
            radar_metrics.append(
                {
                    "id": "cascading_failure",
                    "label": "Cascade resilience",
                    "value": radar.cascading_failure,
                    "color": _METRIC_COLORS["cascading_failure"],
                },
            )
        if radar.system_degradation is not None:
            radar_metrics.append(
                {
                    "id": "system_degradation",
                    "label": "Degradation",
                    "value": radar.system_degradation,
                    "color": _METRIC_COLORS["system_degradation"],
                },
            )

    return {
        "metadata": report.metadata.model_dump(),
        "highlights": report.highlights.model_dump(),
        "experiment_table": [row.model_dump() for row in report.experiment_table],
        "metrics_radar": radar_metrics,
        "timeline": [event.model_dump() for event in report.timeline],
        "agent_graph": report.agent_graph.model_dump(),
        "checkpoint_steps": [step.model_dump() for step in report.checkpoint_steps],
        "key_findings": [finding.model_dump() for finding in report.key_findings],
        "markdown_report": report.markdown_report,
        "export_paths": {
            "summary_csv": report.csv_summary_path,
        },
        "score_colors": {
            "excellent": "#10B981",
            "good": "#3B82F6",
            "fair": "#F59E0B",
            "poor": "#EF4444",
        },
    }


def score_color(score: float) -> str:
    """Map a 0–100 score to a hex color for UI badges."""
    if score >= 80:
        return "#10B981"
    if score >= 60:
        return "#3B82F6"
    if score >= 40:
        return "#F59E0B"
    return "#EF4444"
