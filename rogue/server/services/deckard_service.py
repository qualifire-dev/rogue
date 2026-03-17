import os
from typing import Optional

import requests
from loguru import logger
from rogue_sdk.types import EvaluationResults, ReportSummaryRequest


class DeckardService:
    @staticmethod
    def report_summary(
        request: ReportSummaryRequest,
        evaluation_results: EvaluationResults,
    ):
        logger.info(
            "Reporting summary to Rogue Security",
        )

        # Map policy evaluation results to red team scan format
        # expected by the Rogue Security API
        results = evaluation_results.results
        total_scenarios = len(results)
        failed_scenarios = sum(1 for r in results if not r.passed)

        breakdown: list[dict[str, object]] = []
        for r in results:
            flagged = sum(1 for c in r.conversations if not c.passed)
            total = len(r.conversations)
            success_rate = flagged / total if total > 0 else 0.0
            breakdown.append(
                {
                    "name": r.scenario.scenario,
                    "vulnerability_id": r.scenario.scenario_type or "policy",
                    "cvss_score": success_rate * 10,
                    "severity": (
                        "high"
                        if success_rate > 0.5
                        else "medium" if success_rate > 0 else "low"
                    ),
                    "description": r.scenario.expected_outcome or "",
                    "attacks": [],
                    "success_rate": success_rate,
                },
            )

        overall_score = (
            (total_scenarios - failed_scenarios) / total_scenarios * 100
            if total_scenarios > 0
            else 100.0
        )

        payload = {
            "redTeamScan": {
                "protocol": "a2a",
                "scanType": "custom",
                "model": request.judge_model or "unknown",
                "url": "",
                "vulnerabilitiesDetected": failed_scenarios,
            },
            "redTeamReport": {
                "overallSecurityScore": overall_score,
                "criticalFindingCount": 0,
                "highFindingCount": len(
                    [b for b in breakdown if b["severity"] == "high"],
                ),
                "mediumFindingCount": len(
                    [b for b in breakdown if b["severity"] == "medium"],
                ),
                "lowFindingCount": len(
                    [b for b in breakdown if b["severity"] == "low"],
                ),
                "frameworks": [
                    {
                        "name": "Policy Compliance",
                        "total_vulnerabilities": total_scenarios,
                        "total_checked": total_scenarios,
                        "failed_count": failed_scenarios,
                    },
                ],
                "breakdown": breakdown,
            },
        }

        response = requests.post(
            f"{request.rogue_security_base_url}/api/v1/red-team",
            headers={"X-Rogue-API-Key": request.rogue_security_api_key},
            json=payload,
            timeout=300,
        )

        if not response.ok:
            logger.error(
                "Failed to report summary to Rogue Security",
                extra={"response": response.json()},
            )
            raise Exception(
                f"Failed to report summary to Rogue Security: {response.json()}",
            )

        return response.json()

    @staticmethod
    def report_red_team_scan(
        job,
        report,
        rogue_security_api_key: str,
        rogue_security_base_url: Optional[str] = None,
    ):
        """Report red team scan results to Rogue Security platform.

        Args:
            job: RedTeamJob with request and results
            report: RedTeamReport generated from ComplianceReportGenerator
            rogue_security_api_key: API key for Rogue Security
            rogue_security_base_url: Base URL for Rogue Security API
        """
        if not rogue_security_base_url:
            rogue_security_base_url = os.getenv(
                "ROGUE_SECURITY_URL",
                "https://app.rogue.security",
            )

        logger.info("Reporting red team scan to Rogue Security")

        results = job.results

        payload = {
            "redTeamScan": {
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
                        "name": v.vulnerability_name,
                        "passed": v.passed,
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
            "redTeamReport": {
                "criticalFindingCount": report.highlights.critical_count,
                "highFindingCount": report.highlights.high_count,
                "mediumFindingCount": report.highlights.medium_count,
                "lowFindingCount": report.highlights.low_count,
                "frameworks": [
                    {
                        "name": fc.framework_name,
                        "total_vulnerabilities": fc.total_count,
                        "total_checked": fc.tested_count,
                        "failed_count": fc.tested_count - fc.passed_count,
                    }
                    for fc in report.framework_coverage
                ],
                "overallSecurityScore": report.highlights.overall_score,
                "breakdown": [
                    {
                        "name": vt.vulnerability_name,
                        "vulnerability_id": vt.vulnerability_id,
                        "cvss_score": vt.success_rate,
                        "severity": vt.severity or "low",
                        "description": ", ".join(vt.attacks_used),
                        "attacks": vt.attacks_used,
                        "success_rate": vt.success_rate,
                    }
                    for vt in report.vulnerability_table
                ],
            },
        }

        response = requests.post(
            f"{rogue_security_base_url}/api/v1/red-team",
            headers={"X-Rogue-API-Key": rogue_security_api_key},
            json=payload,
            timeout=300,
        )

        if not response.ok:
            try:
                body = response.json()
            except Exception:
                body = response.text
            logger.error(
                "Failed to report red team scan to Rogue Security",
                extra={
                    "status_code": response.status_code,
                    "response": body,
                },
            )
            raise Exception(
                f"Failed to report red team scan to Rogue Security: "
                f"{response.status_code} {body}",
            )

        try:
            return response.json()
        except Exception:
            logger.error(
                "Rogue Security returned non-JSON response",
                extra={
                    "status_code": response.status_code,
                    "response_text": response.text[:500],
                },
            )
            raise Exception(
                f"Rogue Security returned non-JSON response: "
                f"{response.status_code} {response.text[:500]}",
            )
