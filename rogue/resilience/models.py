"""
Core data models for the Rogue Resilience evaluation system.

These models define experiment traces, metric results, and aggregated
resilience outcomes produced by the orchestrator.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from rogue.injectors.base_injector import InjectorId


class ArchitectureId(str, Enum):
    """Multi-agent architecture profiles (Phase 2 expands usage)."""

    SINGLE_AGENT = "single_agent"
    HIERARCHICAL = "hierarchical"
    PEER_TO_PEER = "peer_to_peer"
    SUPERVISOR_WORKER = "supervisor_worker"
    ROUTER_SPECIALIST = "router_specialist"


class ResilienceMetricId(str, Enum):
    """Registered resilience metric identifiers."""

    DETECTION = "detection"
    CONTAINMENT = "containment"
    RECOVERY = "recovery"
    CASCADING_FAILURE = "cascading_failure"
    SYSTEM_DEGRADATION = "system_degradation"


class TraceEventType(str, Enum):
    """Types of events recorded in an experiment trace."""

    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    INJECTION = "injection"
    DETECTION = "detection"
    CONTAINMENT = "containment"
    RECOVERY = "recovery"
    BASELINE = "baseline"
    CHECKPOINT = "checkpoint"
    ERROR = "error"


class TraceEvent(BaseModel):
    """Single event in an experiment trace."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_id: str = "default"
    event_type: TraceEventType
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    """Outcome of running a baseline, fault, or recovery task."""

    success: bool = False
    response: str = ""
    error: Optional[str] = None
    duration_ms: float = 0.0


class MetricResult(BaseModel):
    """Result of measuring a single resilience metric."""

    metric_id: ResilienceMetricId
    passed: bool = False
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Normalized score from 0 (worst) to 1 (best)",
    )
    value: Optional[float] = Field(
        default=None,
        description="Raw metric value (e.g. latency in seconds)",
    )
    reason: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class ExperimentTrace(BaseModel):
    """
    Full trace for one injector experiment run.

    Attributes:
        experiment_id: Unique identifier for this experiment.
        architecture: Architecture profile under test.
        injector: Fault strategy applied.
        target_agent_id: Agent that received the injection.
        events: Ordered trace events (baseline, injection, messages, recovery).
        baseline_result: Outcome of the pre-fault baseline task.
        fault_result: Outcome during the fault window.
        recovery_result: Outcome of post-teardown validation.
    """

    experiment_id: str = Field(default_factory=lambda: str(uuid4()))
    architecture: ArchitectureId = ArchitectureId.SINGLE_AGENT
    injector: InjectorId | str
    target_agent_id: str = "default"
    events: list[TraceEvent] = Field(default_factory=list)
    baseline_result: Optional[TaskResult] = None
    fault_result: Optional[TaskResult] = None
    recovery_result: Optional[TaskResult] = None


class ExperimentResult(BaseModel):
    """Aggregated outcome for a single injector experiment."""

    experiment_id: str
    injector_id: InjectorId | str
    injector_name: str
    architecture: ArchitectureId
    target_agent_id: str
    trace: ExperimentTrace
    metrics: list[MetricResult] = Field(default_factory=list)
    composite_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Weighted composite resilience score (0-100)",
    )
    passed: bool = False


class ResilienceResults(BaseModel):
    """
    Aggregated results across all experiments in a job.

    Attributes:
        total_experiments: Number of experiments executed.
        experiments_passed: Count where all metrics passed.
        overall_score: Mean composite score (0–100) across experiments.
        detection_rate: Mean detection metric score (0–1).
        containment_rate: Mean containment metric score (0–1).
        recovery_rate: Mean recovery metric score (0–1).
        experiments: Per-experiment detailed results.
        metadata: Arbitrary run metadata (architecture, timestamps, etc.).
    """

    total_experiments: int = 0
    experiments_passed: int = 0
    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )
    detection_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Fraction of experiments where rogue behavior was detected",
    )
    containment_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )
    recovery_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )
    cascading_failure_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Mean cascading-failure metric score (higher is better)",
    )
    system_degradation_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Mean system-degradation metric score (higher is better)",
    )
    experiments: list[ExperimentResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_experiment(self, result: ExperimentResult) -> None:
        """
        Incorporate an experiment result and update aggregate statistics.

        Args:
            result: Completed experiment to append and fold into rates/scores.
        """
        self.experiments.append(result)
        self.total_experiments = len(self.experiments)
        self.experiments_passed = sum(1 for e in self.experiments if e.passed)
        if self.experiments:
            self.overall_score = sum(e.composite_score for e in self.experiments) / len(
                self.experiments,
            )
            detection_scores = [
                m.score
                for e in self.experiments
                for m in e.metrics
                if m.metric_id == ResilienceMetricId.DETECTION
            ]
            containment_scores = [
                m.score
                for e in self.experiments
                for m in e.metrics
                if m.metric_id == ResilienceMetricId.CONTAINMENT
            ]
            recovery_scores = [
                m.score
                for e in self.experiments
                for m in e.metrics
                if m.metric_id == ResilienceMetricId.RECOVERY
            ]
            cascade_scores = [
                m.score
                for e in self.experiments
                for m in e.metrics
                if m.metric_id == ResilienceMetricId.CASCADING_FAILURE
            ]
            degradation_scores = [
                m.score
                for e in self.experiments
                for m in e.metrics
                if m.metric_id == ResilienceMetricId.SYSTEM_DEGRADATION
            ]
            self.detection_rate = (
                sum(detection_scores) / len(detection_scores) if detection_scores else 0.0
            )
            self.containment_rate = (
                sum(containment_scores) / len(containment_scores)
                if containment_scores
                else 0.0
            )
            self.recovery_rate = (
                sum(recovery_scores) / len(recovery_scores) if recovery_scores else 0.0
            )
            self.cascading_failure_rate = (
                sum(cascade_scores) / len(cascade_scores) if cascade_scores else 0.0
            )
            self.system_degradation_rate = (
                sum(degradation_scores) / len(degradation_scores)
                if degradation_scores
                else 0.0
            )
