"""Red Team API endpoints - Server-native red team operations."""

import os
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from rogue_sdk.types import (
    EvaluationStatus,
    RedTeamJob,
    RedTeamJobListResponse,
    RedTeamRequest,
    RedTeamResponse,
    StructuredSummary,
)

from ...common.logging import get_logger, set_request_context
from ..models.api_format import ServerSummaryGenerationResponse
from ..services.qualifire_service import QualifireService
from ..services.red_team_service import RedTeamService

router = APIRouter(prefix="/red-team", tags=["red-team"])
logger = get_logger(__name__)


@lru_cache(1)
def get_red_team_service():
    """Get or create the red team service singleton."""
    return RedTeamService()


@router.post("", response_model=RedTeamResponse)
async def create_red_team_scan(
    request: RedTeamRequest,
    background_tasks: BackgroundTasks,
    red_team_service: RedTeamService = Depends(get_red_team_service),
):
    """
    Create a new red team scan job.

    This endpoint creates a red team scan job that will test the target agent
    for security vulnerabilities using the specified attacks and configuration.
    """
    job_id = str(uuid.uuid4())

    # Set logging context
    vuln_count = len(request.red_team_config.vulnerabilities)
    attack_count = len(request.red_team_config.attacks)

    set_request_context(
        request_id=job_id,
        job_id=job_id,
        agent_url=str(request.evaluated_agent_url),
        scenario_count=vuln_count,  # Use vuln count as scenario count for logging
    )

    # Build extra logging info
    extra_info = {
        "endpoint": "/red-team",
        "method": "POST",
        "agent_url": str(request.evaluated_agent_url),
        "scan_type": request.red_team_config.scan_type,
        "vulnerabilities_count": vuln_count,
        "attacks_count": attack_count,
        "frameworks": request.red_team_config.frameworks,
        "judge_llm": request.judge_llm,
        "attacker_llm": request.attacker_llm,
        "attacks_per_vulnerability": request.red_team_config.attacks_per_vulnerability,
        "max_retries": request.max_retries,
        "timeout_seconds": request.timeout_seconds,
    }

    logger.info("🔴 Creating red team scan job", extra=extra_info)

    # Create job
    job = RedTeamJob(
        job_id=job_id,
        status=EvaluationStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        request=request,
    )

    # Add job and schedule background task
    await red_team_service.add_job(job)
    background_tasks.add_task(red_team_service.run_job, job_id)

    logger.info(
        "✅ Red team scan job created successfully",
        extra={"job_status": "pending", "background_task_scheduled": True},
    )

    return RedTeamResponse(
        job_id=job_id,
        status=EvaluationStatus.PENDING,
        message="Red team scan job created successfully",
    )


@router.get("", response_model=RedTeamJobListResponse)
async def list_red_team_scans(
    status: Optional[EvaluationStatus] = None,
    limit: int = 50,
    offset: int = 0,
    red_team_service: RedTeamService = Depends(get_red_team_service),
):
    """
    List red team scan jobs with optional filtering.

    Args:
        status: Optional status filter
        limit: Maximum number of jobs to return
        offset: Offset for pagination
    """
    jobs = await red_team_service.get_jobs(
        status=status,
        limit=limit,
        offset=offset,
    )
    total = await red_team_service.get_job_count(status=status)

    return RedTeamJobListResponse(jobs=jobs, total=total)


@router.get("/{job_id}", response_model=RedTeamJob)
async def get_red_team_scan(
    job_id: str,
    red_team_service: RedTeamService = Depends(get_red_team_service),
):
    """
    Get a specific red team scan job by ID.

    Args:
        job_id: The unique identifier of the red team scan job
    """
    job = await red_team_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Red team scan job not found")
    return job


@router.delete("/{job_id}")
async def cancel_red_team_scan(
    job_id: str,
    red_team_service: RedTeamService = Depends(get_red_team_service),
):
    """
    Cancel a running or pending red team scan job.

    Args:
        job_id: The unique identifier of the red team scan job to cancel
    """
    success = await red_team_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Red team scan job not found")
    return {"message": "Red team scan job cancelled successfully"}


@router.post("/{job_id}/summary", response_model=ServerSummaryGenerationResponse)
async def generate_red_team_summary(
    job_id: str,
    red_team_service: RedTeamService = Depends(get_red_team_service),
):
    """
    Generate a compliance report summary for a red team scan.

    This endpoint generates a markdown report from red team results,
    mapping findings to security frameworks (OWASP, MITRE, etc.).

    Args:
        job_id: The unique identifier of the red team scan job
    """
    try:
        # Get the red team job
        job = await red_team_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Red team scan job not found")

        if not job.results:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No results available for this job. "
                    "Please wait for the scan to complete."
                ),
            )

        logger.info(
            "Generating red team compliance report",
            extra={
                "job_id": job_id,
                "vulnerabilities_tested": job.results.total_vulnerabilities_tested,
                "vulnerabilities_found": job.results.total_vulnerabilities_found,
                "frameworks": list(job.results.framework_compliance.keys()),
            },
        )

        # Generate compliance report using ComplianceReportGenerator
        from ..red_teaming.report import ComplianceReportGenerator

        report_gen = ComplianceReportGenerator(
            results=job.results,  # type: ignore[arg-type]
            frameworks=(
                list(job.results.framework_compliance.keys())
                if job.results.framework_compliance
                else None
            ),
        )

        # Generate markdown report (available via report_gen.to_markdown())

        # Extract structured data for the UI
        # Get framework reports for structured summary
        framework_reports = {}
        for framework_id in report_gen.frameworks:
            framework_report = report_gen.generate_framework_compliance(framework_id)
            if framework_report:
                framework_reports[framework_id] = framework_report.to_dict()

        # Build structured summary for the TUI
        detailed_breakdown = []
        for vuln_result in job.results.vulnerability_results:
            status = "✅ PASSED" if vuln_result.passed else "❌ FAILED"
            # SDK/server type mismatch
            attacks_attempted = vuln_result.attacks_attempted  # type: ignore  # noqa: E501
            attacks_successful = vuln_result.attacks_successful  # type: ignore  # noqa: E501
            outcome = (
                f"Attempted {attacks_attempted} attacks, "
                f"{attacks_successful} successful"
            )
            detailed_breakdown.append(
                {
                    "scenario": vuln_result.vulnerability_name,
                    "status": status,
                    "outcome": outcome,
                },
            )

        # SDK/server type mismatch
        overall_score = job.results.overall_score  # type: ignore  # noqa: E501
        structured_summary = StructuredSummary(
            overall_summary=(
                f"Red Team Scan: "
                f"{job.results.total_vulnerabilities_tested} "
                f"vulnerabilities tested, "
                f"{job.results.total_vulnerabilities_found} found. "
                f"Overall Score: {overall_score:.1f}%"
            ),
            key_findings=[
                (
                    f"Found {job.results.total_vulnerabilities_found} "
                    f"vulnerabilities"
                ),
                f"Overall security score: {overall_score:.1f}%",
                *(
                    [
                        (
                            f"{framework_id}: "
                            f"{compliance.compliance_score:.1f}% compliant"
                        )
                        for framework_id, compliance in (
                            job.results.framework_compliance.items()
                        )
                    ]
                ),
            ],
            recommendations=[
                "Review all failed vulnerability tests",
                "Implement defenses for detected attack vectors",
                "Consider additional testing for high-risk areas",
            ],
            detailed_breakdown=detailed_breakdown,
        )

        logger.info("Successfully generated red team compliance report")

        # Auto-report to Qualifire if API key is available
        qualifire_api_key = job.request.qualifire_api_key if job.request else None
        if not qualifire_api_key:
            qualifire_api_key = os.getenv("QUALIFIRE_API_KEY")

        report_url = None
        if qualifire_api_key:
            try:
                logger.info(
                    "Auto-reporting red team scan to Qualifire",
                    extra={"job_id": job_id},
                )

                full_report = report_gen.generate_full_report(
                    scan_type=(
                        job.request.red_team_config.scan_type
                        if job.request
                        else "custom"
                    ),
                    random_seed=(
                        job.request.red_team_config.random_seed
                        if job.request and job.request.red_team_config.random_seed
                        else None
                    ),
                )

                result = QualifireService.report_red_team_scan(
                    job=job,
                    report=full_report,
                    qualifire_api_key=qualifire_api_key,
                )

                scan_id = result.get("scan_id")
                if scan_id:
                    base_url = os.getenv(
                        "QUALIFIRE_URL",
                        "https://app.qualifire.ai",
                    )
                    report_url = f"{base_url}/red-team/{scan_id}"
                    logger.info(
                        "Successfully auto-reported to Qualifire",
                        extra={"scan_id": scan_id},
                    )
            except Exception as e:
                logger.warning(
                    "Failed to auto-report to Qualifire (non-fatal)",
                    extra={"error": str(e)},
                )

        return ServerSummaryGenerationResponse(
            summary=structured_summary,
            message="Successfully generated red team compliance report",
            report_url=report_url,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate red team summary")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate red team summary: {str(e)}",
        )


class ReportToQualifireRequest(BaseModel):
    qualifire_api_key: str
    qualifire_url: str = ""


class ReportToQualifireResponse(BaseModel):
    success: bool
    scan_id: Optional[str] = None
    report_id: Optional[str] = None


@router.post(
    "/{job_id}/report-to-qualifire",
    response_model=ReportToQualifireResponse,
)
async def report_red_team_to_qualifire(
    job_id: str,
    request: ReportToQualifireRequest,
    red_team_service: RedTeamService = Depends(get_red_team_service),
):
    """
    Report red team scan results to Qualifire platform.

    Args:
        job_id: The unique identifier of the red team scan job
        request: Contains qualifire_api_key and optional qualifire_url
    """
    try:
        job = await red_team_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Red team scan job not found")

        if not job.results:
            raise HTTPException(
                status_code=400,
                detail="No results available for this job.",
            )

        # Generate report
        from ..red_teaming.report import ComplianceReportGenerator

        report_gen = ComplianceReportGenerator(
            results=job.results,  # type: ignore[arg-type]
            frameworks=(
                list(job.results.framework_compliance.keys())
                if job.results.framework_compliance
                else None
            ),
        )

        scan_type = job.request.red_team_config.scan_type if job.request else "custom"
        random_seed = (
            job.request.red_team_config.random_seed
            if job.request and job.request.red_team_config.random_seed
            else None
        )

        report = report_gen.generate_full_report(
            scan_type=scan_type,
            random_seed=random_seed,
        )

        result = QualifireService.report_red_team_scan(
            job=job,
            report=report,
            qualifire_api_key=request.qualifire_api_key,
            qualifire_url=request.qualifire_url,
        )

        return ReportToQualifireResponse(
            success=True,
            scan_id=result.get("scan_id"),
            report_id=result.get("report_id"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to report red team scan to Qualifire")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to report to Qualifire: {str(e)}",
        )


@router.get("/{job_id}/report")
async def get_red_team_report(
    job_id: str,
    red_team_service: RedTeamService = Depends(get_red_team_service),
):
    """
    Get the comprehensive red team report for a completed scan.

    This endpoint returns the full report with all sections including
    highlights, key findings, vulnerability table, and framework coverage.
    The report is formatted for TUI consumption.

    Args:
        job_id: The unique identifier of the red team scan job

    Returns:
        Full report data structure formatted for TUI display
    """
    try:
        # Get the red team job
        job = await red_team_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Red team scan job not found")

        if not job.results:
            raise HTTPException(
                status_code=400,
                detail="No results available for this job. Please wait for the scan to complete.",  # noqa: E501
            )

        logger.info(
            "Generating comprehensive red team report",
            extra={
                "job_id": job_id,
                "vulnerabilities_tested": job.results.total_vulnerabilities_tested,
                "vulnerabilities_found": job.results.total_vulnerabilities_found,
            },
        )

        # Generate full report using ComplianceReportGenerator
        from ..red_teaming.report import ComplianceReportGenerator
        from ..red_teaming.report.tui_formatter import format_for_tui

        report_gen = ComplianceReportGenerator(
            results=job.results,  # type: ignore[arg-type]
            frameworks=(
                list(job.results.framework_compliance.keys())
                if job.results.framework_compliance
                else None
            ),
            judge_llm=job.request.judge_llm if job.request else None,
            judge_llm_auth=None,  # Auth will come from service configuration
        )

        # Generate full report
        scan_type = job.request.red_team_config.scan_type if job.request else "custom"
        random_seed = (
            job.request.red_team_config.random_seed
            if job.request and job.request.red_team_config.random_seed
            else None
        )

        full_report = report_gen.generate_full_report(
            scan_type=scan_type,
            random_seed=random_seed,
        )

        # Format for TUI
        tui_report = format_for_tui(full_report)

        logger.info("Successfully generated comprehensive red team report")

        return tui_report

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate red team report")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate red team report: {str(e)}",
        )
