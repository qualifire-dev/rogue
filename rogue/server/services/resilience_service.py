"""Resilience Service — manages resilience experiment jobs."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from rogue_sdk.types import (
    EvaluationStatus,
    ResilienceJob,
    WebSocketEventType,
    WebSocketMessage,
)

from ...common.logging import get_logger, set_job_context
from ..core.resilience_orchestrator import ServerResilienceOrchestrator
from ..websocket.manager import get_websocket_manager
from .job_store import JobStore

logger = get_logger(__name__)


class ResilienceService:
    """
    Service for managing resilience experiment jobs.

    Handles job CRUD, background execution via ``ServerResilienceOrchestrator``,
    WebSocket progress broadcasts, and JSON persistence under
    ``<workdir>/jobs/resilience/``.
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.websocket_manager = get_websocket_manager()
        self._lock = asyncio.Lock()
        self._store: JobStore[ResilienceJob] = JobStore("resilience", ResilienceJob)
        self.jobs: Dict[str, ResilienceJob] = self._store.load_all()
        for job in self.jobs.values():
            self._store.save(job)

    async def add_job(self, job: ResilienceJob) -> None:
        """Add a new resilience job."""
        async with self._lock:
            self.jobs[job.job_id] = job
        self._store.save(job)

    async def get_job(self, job_id: str) -> Optional[ResilienceJob]:
        """Get a resilience job by ID."""
        async with self._lock:
            return self.jobs.get(job_id)

    async def get_jobs(
        self,
        status: Optional[EvaluationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ResilienceJob]:
        """List resilience jobs with optional status filtering."""
        async with self._lock:
            jobs = list(self.jobs.values())
        if status:
            jobs = [job for job in jobs if job.status == status]
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        return jobs[offset : offset + limit]

    async def get_job_count(self, status: Optional[EvaluationStatus] = None) -> int:
        """Count resilience jobs, optionally filtered by status."""
        async with self._lock:
            if status:
                return len([job for job in self.jobs.values() if job.status == status])
            return len(self.jobs)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running resilience job."""
        job = await self.get_job(job_id)
        if not job:
            return False
        if job.status in (EvaluationStatus.PENDING, EvaluationStatus.RUNNING):
            job.status = EvaluationStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            self._notify_job_update(job)
        return True

    async def run_job(self, job_id: str) -> None:
        """
        Execute a resilience experiment job in the background.

        Updates job status, streams orchestrator events to WebSocket clients,
        and persists results. Failures are logged and recorded on the job.

        Args:
            job_id: Identifier of the job to run.
        """
        job = await self.get_job(job_id)
        if not job:
            return

        try:
            set_job_context(
                job_id=job_id,
                agent_url=str(job.request.evaluated_agent_url or "python"),
            )
            logger.info(
                "Starting resilience job",
                extra={
                    "job_id": job_id,
                    "injectors": job.request.resilience_config.injectors,
                },
            )

            job.status = EvaluationStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            self._notify_job_update(job)

            orchestrator = ServerResilienceOrchestrator(
                protocol=job.request.evaluated_agent_protocol,
                transport=job.request.evaluated_agent_transport,
                evaluated_agent_url=str(job.request.evaluated_agent_url or ""),
                evaluated_agent_auth_type=job.request.evaluated_agent_auth_type,
                evaluated_agent_auth_credentials=job.request.evaluated_agent_auth_credentials,
                resilience_config=job.request.resilience_config,
                judge_llm=job.request.judge_llm,
                judge_llm_api_key=job.request.judge_llm_api_key,
                judge_llm_api_base=job.request.judge_llm_api_base,
                judge_llm_api_version=job.request.judge_llm_api_version,
                business_context=job.request.business_context,
                python_entrypoint_file=job.request.python_entrypoint_file,
            )

            async for update_type, data in orchestrator.run_experiments():
                if update_type == "status":
                    if isinstance(data, dict) and "progress" in data:
                        job.progress = float(data["progress"])
                    self._notify_job_update(job)
                elif update_type == "trace":
                    if isinstance(data, dict):
                        job.traces.append(data)
                    self._send_websocket(
                        job_id,
                        WebSocketEventType.RESILIENCE_TRACE_UPDATE,
                        data,
                    )
                elif update_type == "experiment":
                    job.progress = min(0.95, job.progress + 0.1)
                    self._notify_job_update(job)
                elif update_type == "results":
                    if hasattr(data, "model_dump"):
                        job.results = data.model_dump()
                    elif isinstance(data, dict):
                        job.results = data
                    job.progress = 1.0
                    self._notify_job_update(job)

            job.status = EvaluationStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            self._notify_job_update(job)
            logger.info("Resilience job completed", extra={"job_id": job_id})

        except Exception as exc:
            logger.exception("Resilience job failed", extra={"job_id": job_id})
            job.status = EvaluationStatus.FAILED
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            self._notify_job_update(job)

    def _notify_job_update(self, job: ResilienceJob) -> None:
        self._store.save(job)
        message = WebSocketMessage(
            type=WebSocketEventType.JOB_UPDATE,
            job_id=job.job_id,
            data={
                "status": job.status.value,
                "progress": job.progress,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": (
                    job.completed_at.isoformat() if job.completed_at else None
                ),
                "error_message": job.error_message,
            },
        )
        asyncio.create_task(
            self.websocket_manager.broadcast_to_job(job.job_id, message),
        )

    def _send_websocket(
        self,
        job_id: str,
        event_type: WebSocketEventType,
        data: Any,
    ) -> None:
        try:
            message = WebSocketMessage(type=event_type, data=data, job_id=job_id)
            asyncio.create_task(
                self.websocket_manager.broadcast_to_job(job_id, message),
            )
        except Exception as exc:
            logger.error(
                f"Failed to send websocket message: {exc}",
                extra={"job_id": job_id, "event_type": event_type.value},
            )
