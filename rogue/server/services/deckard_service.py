import os
from collections import defaultdict
from typing import Any, Optional

import requests
from loguru import logger

from rogue_sdk.types import EvaluationResults, ReportSummaryRequest

_MAX_CONTENT_BYTES = 64 * 1024


def _safe_content(value: Any) -> str:
    """Cap individual message content to bound the HTTP payload size.

    The cap is in UTF-8 bytes, not characters, so a long string of
    multibyte codepoints can't slip past the limit. Truncation always
    falls on a codepoint boundary (no mojibake on the wire).
    """
    if value is None:
        return ""
    text = value if isinstance(value, str) else str(value)
    encoded = text.encode("utf-8")
    if len(encoded) <= _MAX_CONTENT_BYTES:
        return text
    truncated = encoded[:_MAX_CONTENT_BYTES].decode("utf-8", errors="ignore")
    return truncated + "…[truncated]"


class DeckardService:
    @staticmethod
    def _build_red_team_conversations(
        results: Any,
    ) -> list[dict[str, object]]:
        """Group per-turn conversation log dicts into per-session transcripts.

        `results.conversations` is a list of dicts produced by the red-team
        orchestrator (one per turn). We key by `session_id` so each row in
        the destination table corresponds to one full conversation between
        the evaluator and the agent under test.
        """
        raw_turns = getattr(results, "conversations", None) or []
        vuln_results = getattr(results, "vulnerability_results", None) or []
        vuln_name_by_id: dict[str, str] = {
            vr.vulnerability_id: vr.vulnerability_name for vr in vuln_results
        }

        turns_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
        meta_by_session: dict[str, dict[str, Any]] = {}
        for turn in raw_turns:
            if not isinstance(turn, dict):
                continue
            session_id = str(turn.get("session_id") or "")
            turns_by_session[session_id].append(turn)
            if session_id not in meta_by_session:
                meta_by_session[session_id] = {
                    "vulnerability_id": turn.get("vulnerability_id"),
                    "attack_id": turn.get("attack_id"),
                    "is_multi_turn": turn.get("is_multi_turn"),
                    "is_premium": turn.get("is_premium"),
                }

        conversations_payload: list[dict[str, object]] = []
        for session_id, turns in turns_by_session.items():
            ordered = sorted(
                turns,
                # Use explicit defaults so a `turn=0` doesn't fall through to
                # `attempt` via Python's `or` truthiness.
                key=lambda t: t.get("turn", t.get("attempt", 0)),
            )
            messages: list[dict[str, object]] = []
            any_detected = False
            any_eval_signal = False
            last_eval: dict[str, Any] = {}
            for t in ordered:
                msg = t.get("message")
                resp = t.get("response")
                if msg is not None:
                    messages.append(
                        {
                            "role": "user",
                            "content": _safe_content(msg),
                            "timestamp": None,
                        },
                    )
                if resp is not None:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": _safe_content(resp),
                            "timestamp": None,
                        },
                    )
                ev = t.get("evaluation") or {}
                if isinstance(ev, dict):
                    last_eval = ev
                    if "vulnerability_detected" in ev:
                        any_eval_signal = True
                        if ev.get("vulnerability_detected"):
                            any_detected = True

            meta = meta_by_session.get(session_id, {})
            vuln_id = str(meta.get("vulnerability_id") or "")
            scenario_name = vuln_name_by_id.get(vuln_id, vuln_id or "unknown")
            reason = None
            if isinstance(last_eval, dict):
                reason = last_eval.get("reason") or last_eval.get("explanation")

            # Symmetry with the attack-finding path: default to "not safe"
            # when no detection signal exists. A session only counts as
            # passed if at least one evaluation explicitly cleared it.
            passed = any_eval_signal and not any_detected

            conversations_payload.append(
                {
                    "scenario_name": scenario_name,
                    "scenario_type": vuln_id or None,
                    "passed": passed,
                    "reason": reason,
                    "conversation_id": session_id or None,
                    "messages": messages,
                    "metadata": {
                        "attack_id": meta.get("attack_id"),
                        "is_multi_turn": meta.get("is_multi_turn"),
                        "is_premium": meta.get("is_premium"),
                        "vulnerability_detected": any_detected,
                        "evaluator_ran": any_eval_signal,
                        "last_evaluation": last_eval or None,
                    },
                },
            )

        return conversations_payload

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
                        else "medium"
                        if success_rate > 0
                        else "low"
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

        conversations_payload: list[dict[str, object]] = []
        for r in results:
            attempts_total = len(r.conversations)
            for attempt_index, conv in enumerate(r.conversations):
                conversations_payload.append(
                    {
                        "scenario_name": r.scenario.scenario,
                        "scenario_type": r.scenario.scenario_type or "policy",
                        "passed": conv.passed,
                        "reason": conv.reason,
                        # Stable per-conversation UUID minted by the driver
                        # (``BaseEvaluatorAgent._get_conversation_context_id``)
                        # — lets the platform dedupe attempts across
                        # re-reports and link back to a specific run.
                        "conversation_id": conv.context_id,
                        "messages": [
                            {
                                "role": m.role,
                                "content": _safe_content(m.content),
                                "timestamp": m.timestamp,
                            }
                            for m in conv.messages.messages
                        ],
                        "metadata": {
                            "expected_outcome": r.scenario.expected_outcome,
                            # Per-attempt position within ``r.conversations``
                            # so the platform can render "attempt 2 of 5"
                            # under a single scenario row.
                            "attempt_index": attempt_index,
                            "attempts_total": attempts_total,
                        },
                    },
                )

        # Also include red-team attack transcripts if present on
        # EvaluationResults (populated when a red-team phase ran alongside
        # policy evaluation).
        for attack in evaluation_results.red_teaming_results or []:
            conversations_payload.append(
                {
                    "scenario_name": attack.vulnerability_type,
                    "scenario_type": attack.owasp_category,
                    "passed": (attack.metric_score or 0.0) >= 1.0,
                    "reason": attack.metric_reason,
                    "conversation_id": attack.conversation_id,
                    "messages": [
                        {
                            "role": m.role,
                            "content": _safe_content(m.content),
                            "timestamp": m.timestamp,
                        }
                        for m in attack.reproduction_steps
                    ],
                    "metadata": {
                        "severity": (
                            attack.severity.value if attack.severity else None
                        ),
                        "attack_method": attack.attack_method,
                        "strategy_id": attack.strategy_id,
                        "strategy_complexity": attack.strategy_complexity,
                        "attack_success_rate": attack.attack_success_rate,
                        "risk_score": attack.risk_score,
                        "metric_score": attack.metric_score,
                        "remediation": attack.remediation,
                    },
                },
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
            "conversations": conversations_payload,
        }

        target_url = f"{request.rogue_security_base_url}/api/v1/red-team"
        logger.info(
            "Posting summary to Rogue Security",
            extra={
                "url": target_url,
                "conversations_count": len(conversations_payload),
            },
        )
        response = requests.post(
            target_url,
            headers={"X-Rogue-API-Key": request.rogue_security_api_key},
            json=payload,
            timeout=300,
        )

        if not response.ok:
            logger.error(
                "Failed to report summary to Rogue Security",
                extra={"response": response.json(), "url": target_url},
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
            "conversations": DeckardService._build_red_team_conversations(
                results,
            ),
        }

        target_url = f"{rogue_security_base_url}/api/v1/red-team"
        logger.info(
            "Posting red team scan to Rogue Security",
            extra={
                "url": target_url,
                "conversations_count": len(payload.get("conversations") or []),
            },
        )
        response = requests.post(
            target_url,
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
                    "url": target_url,
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
