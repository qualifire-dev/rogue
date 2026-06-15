"""Resilience API endpoints — chaos experiment job management."""

import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from rogue_sdk.types import (
    EvaluationStatus,
    ResilienceJob,
    ResilienceJobListResponse,
    ResilienceRequest,
    ResilienceResponse,
)

from ...common.logging import get_logger, set_request_context
from ..services.resilience_service import ResilienceService

router = APIRouter(prefix="/resilience", tags=["resilience"])
logger = get_logger(__name__)


@lru_cache(1)
def get_resilience_service() -> ResilienceService:
    """Return the resilience service singleton."""
    return ResilienceService()


@router.post("", response_model=ResilienceResponse)
async def create_resilience_job(
    request: ResilienceRequest,
    background_tasks: BackgroundTasks,
    resilience_service: ResilienceService = Depends(get_resilience_service),
) -> ResilienceResponse:
    """
    Create a new resilience experiment job.

    Runs configured fault injectors against the target agent and measures
    detection, containment, and recovery metrics.
    """
    job_id = str(uuid.uuid4())
    set_request_context(
        request_id=job_id,
        job_id=job_id,
        agent_url=str(request.evaluated_agent_url or request.python_entrypoint_file),
    )

    logger.info(
        "Creating resilience job",
        extra={
            "job_id": job_id,
            "injectors": request.resilience_config.injectors,
            "protocol": request.evaluated_agent_protocol.value,
        },
    )

    job = ResilienceJob(
        job_id=job_id,
        status=EvaluationStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        request=request,
    )
    await resilience_service.add_job(job)
    background_tasks.add_task(resilience_service.run_job, job_id)

    return ResilienceResponse(
        job_id=job_id,
        status=EvaluationStatus.PENDING,
        message="Resilience experiment job created successfully",
    )


@router.get("/{job_id}", response_model=ResilienceJob)
async def get_resilience_job(
    job_id: str,
    resilience_service: ResilienceService = Depends(get_resilience_service),
) -> ResilienceJob:
    """Get a resilience job by ID."""
    job = await resilience_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Resilience job not found")
    return job


@router.get("", response_model=ResilienceJobListResponse)
async def list_resilience_jobs(
    status: Optional[EvaluationStatus] = None,
    limit: int = 50,
    offset: int = 0,
    resilience_service: ResilienceService = Depends(get_resilience_service),
) -> ResilienceJobListResponse:
    """List resilience experiment jobs."""
    jobs = await resilience_service.get_jobs(status=status, limit=limit, offset=offset)
    total = await resilience_service.get_job_count(status=status)
    return ResilienceJobListResponse(jobs=jobs, total=total)


@router.post("/{job_id}/cancel")
async def cancel_resilience_job(
    job_id: str,
    resilience_service: ResilienceService = Depends(get_resilience_service),
) -> dict[str, str]:
    """Cancel a pending or running resilience job."""
    cancelled = await resilience_service.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Resilience job not found")
    return {"message": "Resilience job cancelled", "job_id": job_id}
