"""Resilience API endpoints — chaos experiment job management."""

import asyncio
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from rogue_sdk.types import (
    EvaluationStatus,
    ResilienceJob,
    ResilienceJobListResponse,
    ResilienceRequest,
    ResilienceResponse,
)

from ...common.logging import get_logger, set_request_context
from ..services.resilience_scenario_service import (
    ResilienceScenarioService,
    ResilienceScenarioTemplate,
)
from ..services.resilience_service import ResilienceService
from rogue.injectors.registry import list_injectors
from rogue.injectors.premium_catalog import list_premium_injectors

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


class ResilienceScenarioGenerateRequest(BaseModel):
    """Request to generate resilience experiment templates."""

    business_context: str
    model: str = "openai/gpt-4o-mini"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    count: int = Field(default=5, ge=1, le=15)


class ResilienceScenarioGenerateResponse(BaseModel):
    """Generated resilience experiment templates."""

    scenarios: list[ResilienceScenarioTemplate]
    message: str = "Scenarios generated successfully"


@router.get("/injectors/catalog")
async def list_injector_catalog() -> dict:
    """List built-in, premium, and registered custom injectors."""
    entries = list_injectors(include_premium=True)
    return {
        "injectors": [
            {
                "id": str(item.id.value if hasattr(item.id, "value") else item.id),
                "name": item.name,
                "description": item.description,
                "premium": item.premium,
                "custom": item.custom,
            }
            for item in entries
        ],
        "premium_metadata": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "deckard_required": p.deckard_required,
            }
            for p in list_premium_injectors()
        ],
    }


@router.post("/scenarios/generate", response_model=ResilienceScenarioGenerateResponse)
async def generate_resilience_scenarios(
    request: ResilienceScenarioGenerateRequest,
) -> ResilienceScenarioGenerateResponse:
    """Generate resilience experiment templates from business context."""
    service = ResilienceScenarioService(
        model=request.model,
        api_key=request.api_key,
        api_base=request.api_base,
    )
    scenarios = await asyncio.to_thread(
        service.generate,
        request.business_context,
        request.count,
    )
    return ResilienceScenarioGenerateResponse(scenarios=scenarios)


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


@router.get("/{job_id}/report")
async def get_resilience_report(
    job_id: str,
    resilience_service: ResilienceService = Depends(get_resilience_service),
) -> dict:
    """
    Get the comprehensive resilience report for a completed experiment job.

    Returns scorecard, per-injector breakdown, timeline, agent graph, and
    checkpoint replay data formatted for the web dashboard.
    """
    job = await resilience_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Resilience job not found")

    if not job.results:
        raise HTTPException(
            status_code=400,
            detail="No results available for this job. Wait for the experiment to complete.",
        )

    logger.info(
        "Generating resilience report",
        extra={
            "job_id": job_id,
            "experiments": job.results.get("total_experiments"),
        },
    )

    try:
        from ..resilience.report import ResilienceReportGenerator, format_for_web

        config = job.request.resilience_config
        generator = ResilienceReportGenerator.from_results_dict(
            job.results,
            architecture=config.architecture,
            target_agent_id=config.target_agent_id,
            injectors=config.injectors,
            experiments_per_injector=config.experiments_per_injector,
            use_heuristics=config.use_heuristics,
            enable_checkpoint_recovery=config.enable_checkpoint_recovery,
            judge_llm=job.request.judge_llm,
        )
        full_report = generator.generate_full_report()
        return format_for_web(full_report)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to generate resilience report", extra={"job_id": job_id})
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate resilience report: {exc}",
        ) from exc
