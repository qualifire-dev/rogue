"""
LLM API endpoints - Server-native LLM operations.

This module provides REST API endpoints for LLM operations.
"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from rogue_sdk.types import (
    EvaluationResults,
    ReportSummaryRequest,
    ReportSummaryResponse,
    ScenarioGenerationRequest,
    ScenarioGenerationResponse,
    StructuredSummary,
    SummaryGenerationRequest,
)

from rogue.server.api.evaluation import get_evaluation_service
from rogue.server.services.evaluation_service import EvaluationService

from ...common.logging import get_logger
from ..models.api_format import ServerSummaryGenerationResponse
from ..services.llm_service import LLMService
from ..services.qualifire_service import QualifireService

router = APIRouter(prefix="/llm", tags=["llm"])
logger = get_logger(__name__)


@router.post("/scenarios", response_model=ScenarioGenerationResponse)
async def generate_scenarios(request: ScenarioGenerationRequest):
    """
    Generate test scenarios based on business context.

    This endpoint replaces direct calls to LLMService.generate_scenarios().
    """
    try:
        logger.info(
            "Generating scenarios via API",
            extra={
                "business_context_length": len(request.business_context),
                "model": request.model,
                "count": request.count,
            },
        )

        scenarios = LLMService.generate_scenarios(
            model=request.model,
            context=request.business_context,
            llm_provider_api_key=request.api_key,
            aws_access_key_id=request.aws_access_key_id,
            aws_secret_access_key=request.aws_secret_access_key,
            aws_region=request.aws_region,
        )

        logger.info(f"Successfully generated {len(scenarios.scenarios)} scenarios")

        return ScenarioGenerationResponse(
            scenarios=scenarios,
            message=f"Successfully generated {len(scenarios.scenarios)} scenarios",
        )

    except Exception as e:
        logger.exception("Failed to generate scenarios")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate scenarios: {str(e)}",
        )


@router.post(
    "/summary",
    response_model=ServerSummaryGenerationResponse,
)
async def generate_summary(
    request: SummaryGenerationRequest,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
) -> ServerSummaryGenerationResponse:
    """
    Generate evaluation summary from results.

    This endpoint replaces direct calls to LLMService.generate_summary_from_results().
    For red team evaluations, returns OWASP report markdown instead of LLM summary.
    """
    try:
        # Get full evaluation results from job if available
        # This is the authoritative source that includes red team data
        evaluation_results = request.results
        job = None

        if request.job_id:
            try:
                job = await evaluation_service.get_job(request.job_id)
                if job:
                    # Use full evaluation_results from job if available
                    if job.evaluation_results:
                        evaluation_results = job.evaluation_results
                        logger.info(
                            "Using full evaluation_results from job",
                            extra={
                                "job_id": request.job_id,
                                "red_team_count": (
                                    len(evaluation_results.red_teaming_results)
                                    if evaluation_results.red_teaming_results
                                    else 0
                                ),
                                "scan_log_count": (
                                    len(evaluation_results.vulnerability_scan_log)
                                    if evaluation_results.vulnerability_scan_log
                                    else 0
                                ),
                            },
                        )
            except Exception as e:  # noqa: BLE001
                logger.debug(
                    "Could not retrieve job",
                    extra={"job_id": request.job_id, "error": str(e)},
                )

        # Determine if this is a red team evaluation
        # Primary method: check evaluation_mode from job if available
        is_red_team = False
        evaluation_mode_str = None

        if job and job.request and job.request.agent_config:
            evaluation_mode = job.request.agent_config.evaluation_mode
            if evaluation_mode:
                from rogue_sdk.types import EvaluationMode

                evaluation_mode_str = (
                    evaluation_mode.value
                    if hasattr(evaluation_mode, "value")
                    else str(evaluation_mode)
                )
                is_red_team = evaluation_mode == EvaluationMode.RED_TEAM
                logger.info(
                    "Retrieved evaluation mode from job",
                    extra={
                        "job_id": request.job_id,
                        "evaluation_mode": evaluation_mode_str,
                        "is_red_team": is_red_team,
                    },
                )

        # Fallback method: infer from results structure
        if not is_red_team:
            has_red_team_results = (
                evaluation_results.red_teaming_results is not None
                and len(evaluation_results.red_teaming_results) > 0
            )
            has_owasp_summary = (
                evaluation_results.owasp_summary is not None
                and len(evaluation_results.owasp_summary) > 0
            )
            has_vulnerability_scan_log = (
                evaluation_results.vulnerability_scan_log is not None
                and len(evaluation_results.vulnerability_scan_log) > 0
            )

            is_red_team = (
                has_red_team_results or has_owasp_summary or has_vulnerability_scan_log
            )

            logger.info(
                "Inferred evaluation type from results",
                extra={
                    "has_red_team_results": has_red_team_results,
                    "has_owasp_summary": has_owasp_summary,
                    "has_vulnerability_scan_log": has_vulnerability_scan_log,
                    "is_red_team": is_red_team,
                },
            )

        logger.info(
            "Determined evaluation type",
            extra={
                "is_red_team": is_red_team,
                "evaluation_mode": evaluation_mode_str,
                "job_id": request.job_id,
            },
        )

        if is_red_team:
            # Generate OWASP report markdown for red team evaluations
            logger.info(
                "Generating OWASP report markdown for red team evaluation",
                extra={
                    "red_teaming_results_count": (
                        len(evaluation_results.red_teaming_results)
                        if evaluation_results.red_teaming_results
                        else 0
                    ),
                    "vulnerability_scan_log_count": (
                        len(evaluation_results.vulnerability_scan_log)
                        if evaluation_results.vulnerability_scan_log
                        else 0
                    ),
                },
            )

            from ..red_teaming.report_generator import OWASPComplianceReport

            # Get OWASP categories from the job if available
            owasp_categories = None
            if job and job.request and job.request.agent_config:
                # SDK/server type mismatch
                owasp_categories = job.request.agent_config.owasp_categories  # type: ignore  # noqa: E501
                logger.info(
                    "Retrieved OWASP categories from job",
                    extra={
                        "categories": owasp_categories,
                        "count": (len(owasp_categories) if owasp_categories else 0),
                    },
                )

            # Use the evaluation_results (from job if available)
            report = OWASPComplianceReport(
                evaluation_results=evaluation_results,
                owasp_categories=owasp_categories,
                judge_llm=request.model,
                judge_llm_api_key=request.api_key,
            )

            logger.info(
                "Created OWASP report",
                extra={
                    "categories_in_report": len(report.owasp_categories),
                    "categories": report.owasp_categories,
                },
            )
            markdown_report = report.to_markdown()

            # Extract key findings from the report
            key_findings = report.get_key_insights()

            # Extract recommendations from the report
            recommendations = report._generate_recommendations()

            # Create detailed breakdown from category summaries
            # Filter out categories with 0 tests as requested by user
            detailed_breakdown = []
            category_summaries = report.get_summary()

            # Filter to only include categories that were actually tested
            tested_categories = {
                cat_id: summary
                for cat_id, summary in category_summaries.items()
                if summary["total_tests"] > 0
            }

            logger.info(
                "Creating detailed breakdown",
                extra={
                    "total_categories": len(category_summaries),
                    "tested_categories": len(tested_categories),
                    "categories": list(tested_categories.keys()),
                },
            )

            for category_id in sorted(tested_categories.keys()):
                cat_summary = tested_categories[category_id]

                # Determine status (we know total_tests > 0 now)
                status = "✅ PASSED" if cat_summary["passed"] else "❌ FAILED"
                # Create outcome description
                vuln_count = cat_summary["vulnerabilities_found"]
                total_tests = cat_summary["total_tests"]
                outcome = (
                    f"Found {vuln_count} vulnerabilit"
                    f"{'ies' if vuln_count != 1 else 'y'} "
                    f"out of {total_tests} tests"
                )

                # Get category name and full OWASP ID for scenario description
                full_owasp_id = report._get_owasp_full_id(category_id)
                scenario_text = f"{full_owasp_id} Scenario"
                detailed_breakdown.append(
                    {
                        "scenario": scenario_text,
                        "status": status,
                        "outcome": outcome,
                    },
                )

            logger.info(
                "Detailed breakdown created",
                extra={
                    "breakdown_count": len(detailed_breakdown),
                    "first_scenario": (
                        detailed_breakdown[0]["scenario"]
                        if detailed_breakdown
                        else None
                    ),
                    "expected_format": (
                        "Should be OWASP category format (LLM01:2025...)"
                    ),
                },
            )

            # Create a StructuredSummary with all fields populated
            summary = StructuredSummary(
                overall_summary=markdown_report,
                key_findings=key_findings,
                recommendations=recommendations,
                detailed_breakdown=detailed_breakdown,
            )

            logger.info("Successfully generated OWASP report markdown")
        else:
            # Generate LLM summary for policy evaluations
            logger.info(
                "Generating summary via API",
                extra={
                    "model": request.model,
                    "results_count": len(request.results.results),
                },
            )

            summary = LLMService.generate_summary_from_results(
                model=request.model,
                results=evaluation_results,
                llm_provider_api_key=request.api_key,
                aws_access_key_id=request.aws_access_key_id,
                aws_secret_access_key=request.aws_secret_access_key,
                aws_region=request.aws_region,
            )

        logger.info("Successfully generated evaluation summary")

        if not request.qualifire_api_key:
            env_api_key = os.getenv("QUALIFIRE_API_KEY")
            if env_api_key:
                request.qualifire_api_key = env_api_key

        if False and request.qualifire_api_key and request.job_id:

            logger.info(
                "Reporting summary to Qualifire",
                extra={"job_id": request.job_id},
            )

            job = await evaluation_service.get_job(request.job_id)

            if not job and not request.judge_model and not request.deep_test:
                raise HTTPException(
                    status_code=400,
                    detail="Job not found and judge model and deep test are not provided",  # noqa: E501
                )

            logger.info(
                "Summary",
                extra={"summary": summary, "results": request.results},
            )

            QualifireService.report_summary(
                ReportSummaryRequest(
                    job_id=request.job_id,
                    structured_summary=summary,
                    deep_test=job.deep_test if job else request.deep_test,
                    start_time=(
                        job.created_at
                        if job is not None
                        else datetime.now(timezone.utc)
                    ),
                    judge_model=job.judge_model if job else request.judge_model,
                    qualifire_url=request.qualifire_url,
                    qualifire_api_key=request.qualifire_api_key,
                ),
                evaluation_results=evaluation_results,
            )

        return ServerSummaryGenerationResponse(
            summary=summary,
            message="Successfully generated evaluation summary",
        )

    except Exception as e:
        logger.exception("Failed to generate summary")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}",
        )


@router.post("/report_summary", response_model=ReportSummaryResponse)
async def report_summary_handler(
    request: ReportSummaryRequest,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
):
    """
    Report summary to Qualifire.
    """
    try:
        job = await evaluation_service.get_job(request.job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Evaluation job not found",
            )

        results = job.results

        if not results or len(results) == 0:
            raise HTTPException(
                status_code=404,
                detail="Evaluation results not found or empty",
            )

        if not request.qualifire_api_key:
            env_api_key = os.getenv("QUALIFIRE_API_KEY")
            if env_api_key:
                request.qualifire_api_key = env_api_key

        QualifireService.report_summary(
            ReportSummaryRequest(
                job_id=request.job_id,
                structured_summary=request.structured_summary,
                deep_test=request.deep_test,
                start_time=job.created_at,
                judge_model=job.judge_model,
                qualifire_api_key=request.qualifire_api_key,
                qualifire_url=request.qualifire_url,
            ),
            evaluation_results=EvaluationResults(results=results),
        )

        return ReportSummaryResponse(
            success=True,
        )
    except Exception as e:
        logger.exception("Failed to report summary")
        raise HTTPException(
            status_code=e.status_code if hasattr(e, "status_code") else 500,
            detail=f"Failed to report summary: {str(e)}",
        )
