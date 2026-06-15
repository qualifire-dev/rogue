"""
Pydantic models for resilience experiment reports.

Structured similarly to ``rogue.server.red_teaming.models.RedTeamReport`` so
the web UI can render scorecards, tables, and charts from a single payload.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ResilienceReportMetadata(BaseModel):
    """Run metadata attached to a resilience report."""

    experiment_date: str
    architecture: str
    architecture_name: str
    target_agent_id: str
    injectors: list[str] = Field(default_factory=list)
    experiments_per_injector: int = 1
    use_heuristics: bool = True
    enable_checkpoint_recovery: bool = False
    judge_llm: Optional[str] = None


class ResilienceReportHighlights(BaseModel):
    """Top-level scorecard metrics for the dashboard hero."""

    overall_score: float = 0.0
    total_experiments: int = 0
    experiments_passed: int = 0
    detection_rate: float = 0.0
    containment_rate: float = 0.0
    recovery_rate: float = 0.0
    cascading_failure_rate: float = 0.0
    system_degradation_rate: float = 0.0
    is_multi_agent: bool = False


class ResilienceReportExperimentRow(BaseModel):
    """Per-injector experiment summary for comparison tables."""

    experiment_id: str
    injector_id: str
    injector_name: str
    architecture: str
    target_agent_id: str
    composite_score: float
    passed: bool
    detection_score: float = 0.0
    containment_score: float = 0.0
    recovery_score: float = 0.0
    cascading_score: Optional[float] = None
    degradation_score: Optional[float] = None


class ResilienceReportMetricRadar(BaseModel):
    """Normalized metric values for radar chart visualization."""

    detection: float = 0.0
    containment: float = 0.0
    recovery: float = 0.0
    cascading_failure: Optional[float] = None
    system_degradation: Optional[float] = None


class ResilienceReportTimelineEvent(BaseModel):
    """Single point on the experiment timeline."""

    timestamp: str
    experiment_id: str
    injector_id: str
    agent_id: str
    event_type: str
    label: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ResilienceReportAgentNode(BaseModel):
    """Node in the agent topology graph."""

    agent_id: str
    role: str
    is_target: bool = False
    is_rogue: bool = False


class ResilienceReportAgentEdge(BaseModel):
    """Directed edge in the agent topology graph."""

    source: str
    target: str
    label: str = ""


class ResilienceReportAgentGraph(BaseModel):
    """Agent topology for graph visualization."""

    nodes: list[ResilienceReportAgentNode] = Field(default_factory=list)
    edges: list[ResilienceReportAgentEdge] = Field(default_factory=list)


class ResilienceReportCheckpointStep(BaseModel):
    """Checkpoint snapshot/restore step for replay scrubber."""

    timestamp: str
    experiment_id: str
    operation: str
    success: bool
    thread_id: Optional[str] = None
    checkpoint_id: Optional[str] = None
    error: Optional[str] = None


class ResilienceReportKeyFinding(BaseModel):
    """Notable weak point from the experiment run."""

    injector_id: str
    injector_name: str
    composite_score: float
    summary: str
    failed_metrics: list[str] = Field(default_factory=list)


class ResilienceReport(BaseModel):
    """Full resilience report consumed by web UI and CLI export."""

    metadata: ResilienceReportMetadata
    highlights: ResilienceReportHighlights
    experiment_table: list[ResilienceReportExperimentRow] = Field(default_factory=list)
    metrics_radar: ResilienceReportMetricRadar = Field(
        default_factory=ResilienceReportMetricRadar,
    )
    timeline: list[ResilienceReportTimelineEvent] = Field(default_factory=list)
    agent_graph: ResilienceReportAgentGraph = Field(
        default_factory=ResilienceReportAgentGraph,
    )
    checkpoint_steps: list[ResilienceReportCheckpointStep] = Field(
        default_factory=list,
    )
    key_findings: list[ResilienceReportKeyFinding] = Field(default_factory=list)
    markdown_report: str = ""
    csv_summary_path: Optional[str] = None
