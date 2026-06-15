"""Tests for ResilienceService job lifecycle semantics."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from rogue.server.services.resilience_service import ResilienceService
from rogue_sdk.types import (
    EvaluationStatus,
    Protocol,
    ResilienceConfig,
    ResilienceJob,
    ResilienceRequest,
)

AGENT = Path("rogue/tests/fixtures/resilience_test_agent.py")


def _make_job(status: EvaluationStatus = EvaluationStatus.PENDING) -> ResilienceJob:
    return ResilienceJob(
        job_id=str(uuid4()),
        status=status,
        created_at=datetime.now(timezone.utc),
        request=ResilienceRequest(
            resilience_config=ResilienceConfig(
                injectors=["policy_violation"],
                use_heuristics=True,
            ),
            evaluated_agent_protocol=Protocol.PYTHON,
            python_entrypoint_file=str(AGENT),
            judge_llm="openai/gpt-4o-mini",
        ),
    )


@pytest.fixture
def service(tmp_path, monkeypatch) -> ResilienceService:
    monkeypatch.chdir(tmp_path)
    return ResilienceService()


@pytest.mark.asyncio
async def test_cancel_job_returns_true_only_when_cancelled(service: ResilienceService) -> None:
    pending = _make_job(EvaluationStatus.PENDING)
    await service.add_job(pending)

    assert await service.cancel_job(pending.job_id) is True
    updated = await service.get_job(pending.job_id)
    assert updated is not None
    assert updated.status == EvaluationStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_job_returns_false_for_terminal_job(service: ResilienceService) -> None:
    completed = _make_job(EvaluationStatus.COMPLETED)
    await service.add_job(completed)

    assert await service.cancel_job(completed.job_id) is False
    updated = await service.get_job(completed.job_id)
    assert updated is not None
    assert updated.status == EvaluationStatus.COMPLETED


@pytest.mark.asyncio
async def test_run_job_skips_already_cancelled_job(
    service: ResilienceService,
    mocker,
) -> None:
    cancelled = _make_job(EvaluationStatus.CANCELLED)
    await service.add_job(cancelled)
    mock_orchestrator = mocker.patch(
        "rogue.server.services.resilience_service.ServerResilienceOrchestrator",
    )

    await service.run_job(cancelled.job_id)

    mock_orchestrator.assert_not_called()
    updated = await service.get_job(cancelled.job_id)
    assert updated is not None
    assert updated.status == EvaluationStatus.CANCELLED


@pytest.mark.asyncio
async def test_run_job_preserves_cancelled_state_after_orchestrator(
    service: ResilienceService,
    mocker,
) -> None:
    job = _make_job(EvaluationStatus.PENDING)
    await service.add_job(job)

    async def fake_experiments():
        current = await service.get_job(job.job_id)
        assert current is not None
        current.status = EvaluationStatus.CANCELLED
        yield "results", {"overall_score": 90.0}

    mock_orchestrator = mocker.patch(
        "rogue.server.services.resilience_service.ServerResilienceOrchestrator",
    )
    mock_orchestrator.return_value.run_experiments = fake_experiments

    await service.run_job(job.job_id)

    updated = await service.get_job(job.job_id)
    assert updated is not None
    assert updated.status == EvaluationStatus.CANCELLED
