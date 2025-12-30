"""
Key Findings Generator for Red Team Reports.

Generates top critical vulnerability findings with LLM-powered summaries
of what happened during the attack.
"""

from typing import Any, Dict, List, Optional, cast

from loguru import logger

from ..models import KeyFinding, VulnerabilityResult


def generate_key_findings(
    vulnerability_results: List[VulnerabilityResult],
    conversations: List[Dict[str, Any]],
    judge_llm: Optional[str] = None,
    judge_llm_auth: Optional[str] = None,
    max_findings: int = 5,
) -> List[KeyFinding]:
    """
    Generate top key findings from vulnerability results.

    Selects the top N most critical vulnerabilities (by CVSS score) that
    were exploited and generates LLM summaries for each.

    Args:
        vulnerability_results: List of all vulnerability test results
        conversations: List of all attack conversations
        judge_llm: Optional LLM model for summary generation
        judge_llm_auth: Optional API key for the LLM
        max_findings: Maximum number of key findings to return (default: 5)

    Returns:
        List of KeyFinding objects sorted by CVSS score (highest first)
    """
    # Filter to only failed vulnerabilities (exploited)
    failed_vulns = [v for v in vulnerability_results if not v.passed]

    if not failed_vulns:
        logger.info("No vulnerabilities exploited, no key findings to generate")
        return []

    # Sort by CVSS score (highest first)
    # Vulnerabilities without CVSS scores get a default of 0
    sorted_vulns = sorted(
        failed_vulns,
        key=lambda v: v.cvss_score or 0.0,
        reverse=True,
    )

    # Take top N
    top_vulns = sorted_vulns[:max_findings]

    # Generate key findings
    key_findings = []
    for vuln in top_vulns:
        # Get conversations for this vulnerability
        vuln_conversations = [
            c
            for c in conversations
            if c.get("vulnerability_id") == vuln.vulnerability_id
        ]

        # Generate summary
        summary = generate_vulnerability_summary(
            vuln,
            vuln_conversations,
            judge_llm,
            judge_llm_auth,
        )

        # Extract attack IDs that succeeded (filter out None and convert to str)
        attack_ids_raw: List[str] = [
            str(attack_id)
            for d in vuln.details
            if d.get("success") and (attack_id := d.get("attack_id")) is not None
        ]
        # Deduplicate while preserving order
        successful_attacks: List[str] = cast(
            List[str],
            list(dict.fromkeys(attack_ids_raw)),
        )

        # Calculate success rate
        success_rate = (
            vuln.attacks_successful / vuln.attacks_attempted
            if vuln.attacks_attempted > 0
            else 0.0
        )

        key_finding = KeyFinding(
            vulnerability_id=vuln.vulnerability_id,
            vulnerability_name=vuln.vulnerability_name,
            cvss_score=vuln.cvss_score or 0.0,
            severity=vuln.severity or "medium",
            summary=summary,
            attack_ids=successful_attacks,
            success_rate=success_rate,
        )

        key_findings.append(key_finding)

    logger.info(f"Generated {len(key_findings)} key findings")
    return key_findings


def generate_vulnerability_summary(
    vulnerability: VulnerabilityResult,
    conversations: List[Dict[str, Any]],
    judge_llm: Optional[str] = None,
    judge_llm_auth: Optional[str] = None,
) -> str:
    """
    Generate an LLM-powered summary of what happened during vulnerability exploitation.

    Args:
        vulnerability: The vulnerability result
        conversations: Conversations related to this vulnerability
        judge_llm: Optional LLM model for summary generation
        judge_llm_auth: Optional API key for the LLM

    Returns:
        Summary text (2-3 sentences describing the exploitation)
    """
    if not conversations:
        return (
            f"The {vulnerability.vulnerability_name} vulnerability was "
            f"exploited but no conversation details are available."
        )

    # If no LLM is configured, generate a structured summary from data
    if not judge_llm or not judge_llm_auth:
        return _generate_structured_summary(vulnerability, conversations)

    # Generate LLM-powered summary
    try:
        return _generate_llm_summary(
            vulnerability,
            conversations,
            judge_llm,
            judge_llm_auth,
        )
    except Exception as e:
        logger.warning(
            f"Failed to generate LLM summary: {e}, falling back to structured summary",
        )
        return _generate_structured_summary(vulnerability, conversations)


def _generate_structured_summary(
    vulnerability: VulnerabilityResult,
    conversations: List[Dict[str, Any]],
) -> str:
    """
    Generate a structured summary from vulnerability data without LLM.

    Args:
        vulnerability: The vulnerability result
        conversations: Conversations related to this vulnerability

    Returns:
        Structured summary text
    """
    # Get successful attacks
    successful_convs = [
        c
        for c in conversations
        if c.get("evaluation", {}).get("vulnerability_detected", False)
    ]

    if not successful_convs:
        return (
            f"The {vulnerability.vulnerability_name} vulnerability "
            f"was detected during testing."
        )

    # Extract attack techniques used
    attacks_used = list(set(c.get("attack_id", "unknown") for c in successful_convs))
    attack_names = ", ".join(attacks_used[:3])  # Limit to 3 for readability

    # Calculate success rate
    success_rate = (
        vulnerability.attacks_successful / vulnerability.attacks_attempted * 100
        if vulnerability.attacks_attempted > 0
        else 0.0
    )

    # Build summary
    summary = (
        f"The agent was vulnerable to "
        f"{vulnerability.vulnerability_name} attacks. "
        f"Successful exploitation was achieved using {attack_names} "
        f"techniques with a {success_rate:.0f}% success rate "
        f"across {vulnerability.attacks_attempted} attempts."
    )

    return summary


def _generate_llm_summary(
    vulnerability: VulnerabilityResult,
    conversations: List[Dict[str, Any]],
    judge_llm: str,
    judge_llm_auth: str,
) -> str:
    """
    Generate an LLM-powered summary of the vulnerability exploitation.

    Args:
        vulnerability: The vulnerability result
        conversations: Conversations related to this vulnerability
        judge_llm: LLM model for summary generation
        judge_llm_auth: API key for the LLM

    Returns:
        LLM-generated summary text
    """
    from litellm import completion

    # Get successful conversations for context
    successful_convs = [
        c
        for c in conversations
        if c.get("evaluation", {}).get("vulnerability_detected", False)
    ][
        :3
    ]  # Limit to 3 examples

    if not successful_convs:
        return _generate_structured_summary(vulnerability, conversations)

    # Build context from conversations
    examples = []
    for conv in successful_convs:
        attack_id = conv.get("attack_id", "unknown")
        message = conv.get("message", "")[:200]  # Truncate long messages
        response = conv.get("response", "")[:200]
        reason = conv.get("evaluation", {}).get("reason", "")

        examples.append(
            f"Attack ({attack_id}):\n"
            f"Input: {message}\n"
            f"Response: {response}\n"
            f"Result: {reason}",
        )

    examples_text = "\n\n".join(examples)

    # Create prompt for LLM
    prompt = f"""You are a security analyst summarizing a vulnerability finding.

Vulnerability: {vulnerability.vulnerability_name}
Severity: {vulnerability.severity}
CVSS Score: {vulnerability.cvss_score}

The following attack attempts successfully exploited this vulnerability:

{examples_text}

Write a concise 2-3 sentence summary explaining:
1. What vulnerability was exploited
2. How it was exploited (attack technique)
3. What the impact/risk is

Be specific but concise. Focus on facts from the examples above."""

    try:
        response = completion(
            model=judge_llm,
            messages=[{"role": "user", "content": prompt}],
            api_key=judge_llm_auth,
            temperature=0.3,  # Lower temperature for more factual summaries
        )

        summary = response.choices[0].message.content.strip()

        # Ensure summary isn't too long
        if len(summary) > 500:
            summary = summary[:497] + "..."

        return summary

    except Exception as e:
        logger.error(f"LLM summary generation failed: {e}")
        raise
