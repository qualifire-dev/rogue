from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
import uuid
from datetime import datetime, timezone

from ..models.api_models import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationJob,
    EvaluationStatus,
    JobListResponse,
)
from ..services.evaluation_service import EvaluationService

router = APIRouter()
evaluation_service = EvaluationService()


@router.post("/evaluations", response_model=EvaluationResponse)
async def create_evaluation(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks,
):
    job_id = str(uuid.uuid4())

    job = EvaluationJob(
        job_id=job_id,
        status=EvaluationStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        request=request,
    )

    evaluation_service.add_job(job)
    background_tasks.add_task(evaluation_service.run_evaluation, job_id)

    return EvaluationResponse(
        job_id=job_id,
        status=EvaluationStatus.PENDING,
        message="Evaluation job created successfully",
    )


@router.get("/evaluations", response_model=JobListResponse)
async def list_evaluations(
    status: Optional[EvaluationStatus] = None,
    limit: int = 50,
    offset: int = 0,
):
    jobs = evaluation_service.get_jobs(status=status, limit=limit, offset=offset)
    total = evaluation_service.get_job_count(status=status)

    return JobListResponse(jobs=jobs, total=total)


@router.get("/evaluations/{job_id}", response_model=EvaluationJob)
async def get_evaluation(job_id: str):
    job = evaluation_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Evaluation job not found")
    return job


@router.delete("/evaluations/{job_id}")
async def cancel_evaluation(job_id: str):
    success = evaluation_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Evaluation job not found")
    return {"message": "Evaluation job cancelled successfully"}
