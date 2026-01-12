import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from rogue_sdk.types import (
    EvaluationJob,
    EvaluationRequest,
    EvaluationResponse,
    EvaluationStatus,
    JobListResponse,
)

from ...common.logging import get_logger, set_request_context
from ..services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])
logger = get_logger(__name__)


@lru_cache(1)
def get_evaluation_service():
    return EvaluationService()


async def enqueue_evaluation(
        request: EvaluationRequest,
        background_tasks: BackgroundTasks,
        evaluation_service: EvaluationService,
        endpoint: str,
):
    job_id = str(uuid.uuid4())

    # Set logging context
    if request.scenarios is not None:
        scenario_count = len(request.scenarios)  # type: ignore[arg-type]
    else:
        scenario_count = 0
    set_request_context(
        request_id=job_id,
        job_id=job_id,
        agent_url=str(request.agent_config.evaluated_agent_url),
        scenario_count=scenario_count,
    )

    # Build extra logging info
    extra_info = {
        "endpoint": "/evaluations",
        "method": "POST",
        "agent_url": str(request.agent_config.evaluated_agent_url),
        "scenario_count": scenario_count,
        "judge_llm": request.agent_config.judge_llm,
        "deep_test_mode": request.agent_config.deep_test_mode,
        "max_retries": request.max_retries,
        "timeout_seconds": request.timeout_seconds,
    }

    logger.info("Creating policy evaluation job", extra=extra_info)

    job = EvaluationJob(
        job_id=job_id,
        status=EvaluationStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        request=request,
        deep_test=request.agent_config.deep_test_mode,
        judge_model=request.agent_config.judge_llm,
    )

    await evaluation_service.add_job(job)
    background_tasks.add_task(evaluation_service.run_job, job_id)

    logger.info(
        "Evaluation job created successfully",
        extra={"job_status": "pending", "background_task_scheduled": True},
    )

    return EvaluationResponse(
        job_id=job_id,
        status=EvaluationStatus.PENDING,
        message="Evaluation job created successfully",
    )


@router.post("", response_model=EvaluationResponse)
async def create_evaluation(
        request: EvaluationRequest,
        background_tasks: BackgroundTasks,
        evaluation_service: EvaluationService = Depends(get_evaluation_service),
):
    return await enqueue_evaluation(
        request=request,
        background_tasks=background_tasks,
        evaluation_service=evaluation_service,
        endpoint="/evaluations",
    )


@router.get("", response_model=JobListResponse)
async def list_evaluations(
        status: Optional[EvaluationStatus] = None,
        limit: int = 50,
        offset: int = 0,
        evaluation_service: EvaluationService = Depends(get_evaluation_service),
):
    jobs = await evaluation_service.get_jobs(
        status=status,
        limit=limit,
        offset=offset,
    )
    total = await evaluation_service.get_job_count(status=status)

    return JobListResponse(jobs=jobs, total=total)


@router.get("/{job_id}", response_model=EvaluationJob)
async def get_evaluation(
        job_id: str,
        evaluation_service: EvaluationService = Depends(get_evaluation_service),
):
    job = await evaluation_service.get_job(job_id)
    logger.info(f"Job: {job}")
    if not job:
        raise HTTPException(status_code=404, detail="Evaluation job not found")
    return job


@router.delete("/{job_id}")
async def cancel_evaluation(
        job_id: str,
        evaluation_service: EvaluationService = Depends(get_evaluation_service),
):
    success = await evaluation_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Evaluation job not found")
    return {"message": "Evaluation job cancelled successfully"}
