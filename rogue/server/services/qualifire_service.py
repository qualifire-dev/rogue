import os
from typing import Optional

import requests
from loguru import logger
from rogue_sdk.types import EvaluationResults, ReportSummaryRequest

from .api_format_service import convert_with_structured_summary


class QualifireService:
    @staticmethod
    def report_summary(
        request: ReportSummaryRequest,
        evaluation_results: EvaluationResults,
    ):
        logger.info(
            "Reporting summary to Qualifire",
        )

        api_evaluation_result = convert_with_structured_summary(
            evaluation_results=evaluation_results,
            structured_summary=request.structured_summary,
            deep_test=request.deep_test,
            start_time=request.start_time,
            judge_model=request.judge_model,
        )

        response = requests.post(
            f"{request.qualifire_url}/api/rogue/v1/report",
            headers={"X-qualifire-key": request.qualifire_api_key},
            json=api_evaluation_result.model_dump(mode="json"),
            timeout=300,
        )

        if not response.ok:
            logger.error(
                "Failed to report summary to Qualifire",
                extra={"response": response.json()},
            )
            raise Exception(f"Failed to report summary to Qualifire: {response.json()}")

        return response.json()

    @staticmethod
    def report_red_team_scan(
        job,
        report,
        qualifire_api_key: str,
        qualifire_url: Optional[str] = None,
    ):
        """Report red team scan results to Qualifire platform.

        Args:
            job: RedTeamJob with request and results
            report: RedTeamReport generated from ComplianceReportGenerator
            qualifire_api_key: API key for Qualifire
            qualifire_url: Base URL for Qualifire API
        """
        if not qualifire_url:
            qualifire_url = os.getenv(
                "QUALIFIRE_BASE_URL",
                "https://app.qualifire.ai",
            )

        logger.info("Reporting red team scan to Qualifire")

        results = job.results

        payload = {
            "rogueRedTeamScan": {
                "protocol": job.request.evaluated_agent_protocol.value,
                "transport": (
                    str(job.request.evaluated_agent_transport)
                    if job.request.evaluated_agent_transport
                    else None
                ),
                "scanType": job.request.red_team_config.scan_type.value,
                "model": job.request.judge_llm,
                "vulnerabilities": [
                    {
                        "id": v.vulnerability_id,
                        "name": v.vulnerability_name,
                        "passed": v.passed,
                        "attacks_attempted": v.attacks_attempted,
                        "attacks_successful": v.attacks_successful,
                        "severity": v.severity,
                        "cvss_score": v.cvss_score,
                    }
                    for v in results.vulnerability_results
                ],
                "attacks": [
                    {
                        "id": a.attack_id,
                        "name": a.attack_name,
                        "times_used": a.times_used,
                        "success_count": a.success_count,
                        "success_rate": a.success_rate,
                    }
                    for a in results.attack_statistics.values()
                ],
                "url": (
                    str(job.request.evaluated_agent_url)
                    if job.request.evaluated_agent_url
                    else ""
                ),
                "vulnerabilitiesDetected": results.total_vulnerabilities_found,
            },
            "rogueRedTeamReport": {
                "criticalFindingCount": report.highlights.critical_count,
                "highFindingCount": report.highlights.high_count,
                "mediumFindingCount": report.highlights.medium_count,
                "lowFindingCount": report.highlights.low_count,
                "frameworks": [
                    {
                        "id": fc.framework_id,
                        "name": fc.framework_name,
                        "compliance_score": fc.compliance_score,
                        "total_vulnerabilities": fc.total_count,
                        "total_checked": fc.tested_count,
                        "passed_count": fc.passed_count,
                        "failed_count": fc.tested_count - fc.passed_count,
                        "status": fc.status,
                    }
                    for fc in report.framework_coverage
                ],
                "overallSecurityScore": report.highlights.overall_score,
                "breakdown": [
                    {
                        "id": vt.vulnerability_id,
                        "vulnerability_id": vt.vulnerability_id,
                        "name": vt.vulnerability_name,
                        "severity": vt.severity or "low",
                        "cvss_score": vt.success_rate,
                        "success_rate": vt.success_rate,
                        "description": ", ".join(vt.attacks_used),
                        "attacks": vt.attacks_used,
                        "attacks_attempted": vt.attacks_attempted,
                        "attacks_successful": vt.attacks_successful,
                        "status": vt.passed,
                    }
                    for vt in report.vulnerability_table
                ],
            },
        }

        response = requests.post(
            f"{qualifire_url}/api/rogue/v1/red-team",
            headers={"X-qualifire-key": qualifire_api_key},
            json=payload,
            timeout=300,
        )

        if not response.ok:
            try:
                body = response.json()
            except Exception:
                body = response.text
            logger.error(
                "Failed to report red team scan to Qualifire",
                extra={
                    "status_code": response.status_code,
                    "response": body,
                },
            )
            raise Exception(
                f"Failed to report red team scan to Qualifire: "
                f"{response.status_code} {body}",
            )

        try:
            return response.json()
        except Exception:
            logger.error(
                "Qualifire returned non-JSON response",
                extra={
                    "status_code": response.status_code,
                    "response_text": response.text[:500],
                },
            )
            raise Exception(
                f"Qualifire returned non-JSON response: "
                f"{response.status_code} {response.text[:500]}",
            )
