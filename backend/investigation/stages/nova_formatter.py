"""
Nova Formatter — AirGuard
=========================
Optional LLM polish stage. Accepts a complete but raw OperationalReport
(produced by the deterministic engine) and rewrites the human-facing fields
into compelling, SRE-grade prose using Amazon Nova Pro.

Architectural contract:
  - Input:  OperationalReport + raw Evidence list
  - Output: OperationalReport (same object, enriched fields)
  - Side effects: None. Pure transformation.
  - Fails gracefully: if Bedrock is unreachable or credentials are absent,
    the unmodified report is returned unchanged.

This stage is intentionally OPTIONAL. The Deterministic Engine produces a
fully valid report without it. Nova is purely a presentation enhancement.
"""
from __future__ import annotations
import json
import re
from typing import List

from backend.investigation.models import OperationalReport, CorrelatedFinding
from backend.core.constants import ConfidenceLevel
from backend.evidence.models import Evidence


def run(report: OperationalReport, evidence: List[Evidence]) -> OperationalReport:
    """
    Polish a raw OperationalReport using Amazon Nova Pro.

    Returns the same report object (fields mutated in-place for efficiency).
    If Nova is unavailable, returns report unchanged — caller never sees a failure.
    """
    # Extract raw task logs to give Nova real evidence context
    raw_task_logs = ""
    for e in evidence:
        if e.source == "airflow_task_logs":
            raw_task_logs += e.normalized_payload.get("logs", "")

    original_corr = "\n".join(
        [f"- {c.finding} (Source: {c.source})" for c in report.correlation_summary]
    )

    prompt = f"""\
You are an expert SRE writing an incident report. Rewrite the following deterministic \
incident details into a highly compelling, readable operational report.
Use the Raw Task Logs to add specific, real-world details (like specific error messages \
or services involved) to your diagnosis to make it detailed and clear. \
Do not invent new facts. Just format and polish.

CRITICAL: The executive summary and root cause MUST explain EXACTLY what happened. \
State which specific task failed, the exact error from the logs, and why it occurred. \
NEVER write generic statements like "A cascade failure occurred" without explaining the \
actual task-level failure and the underlying error. Be extremely specific.

Raw Root Cause: {report.root_cause}
Raw Confidence Reasons: {report.confidence.reasons}
Raw Blast Radius (Workflows): {report.blast_radius.affected_workflows}
Raw Correlation Findings:
{original_corr}
Raw Task Logs (last 2000 chars):
{raw_task_logs[-2000:]}
Suggested Next Step: {report.suggested_next_steps[0] if report.suggested_next_steps else 'Investigate'}

Provide the output strictly as a JSON object with the following schema:
{{
    "executive_summary": "A single paragraph explaining exactly what task failed, what the specific error was, and the root cause.",
    "root_cause": "A single specific sentence (e.g. 'Task X failed repeatedly due to Y timeout error.').",
    "confidence_score": 0.96,
    "confidence_reasons": ["✓ Fact 1", "✓ Fact 2"],
    "blast_radius_summary": ["• 1 workflow impacted", "• 2 downstream tasks blocked"],
    "correlation_findings": [
        {{"finding": "✓ Finding text matching the DAG", "source": "Source Name", "severity": "high"}}
    ]
}}
"""

    try:
        from backend.integrations.aws.client_factory import get_boto3_client
        client = get_boto3_client("bedrock-runtime")

        response = client.invoke_model(
            modelId="us.amazon.nova-pro-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "messages": [{
                    "role": "user",
                    "content": [{
                        "text": (
                            "SYSTEM INSTRUCTION: You are a JSON-only API. "
                            "Only output valid JSON matching the requested schema.\n\n"
                            + prompt
                        )
                    }]
                }]
            }),
        )

        response_body = json.loads(response["body"].read())
        raw_text = (
            response_body
            .get("output", {})
            .get("message", {})
            .get("content", [{}])[0]
            .get("text", "")
        )

        # Robust JSON extraction — strip any markdown fences
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            print("[NovaFormatter] Could not extract JSON from response — keeping raw report.")
            return report

        polished = json.loads(match.group(0))

        # Apply polished fields
        if "executive_summary" in polished:
            report.executive_summary = polished["executive_summary"]
        if "root_cause" in polished:
            report.root_cause = polished["root_cause"]
        if "confidence_score" in polished:
            new_score = float(polished["confidence_score"])
            report.confidence.score = new_score
            if new_score >= 0.8:
                report.confidence.level = ConfidenceLevel.HIGH
            elif new_score >= 0.5:
                report.confidence.level = ConfidenceLevel.MEDIUM
            else:
                report.confidence.level = ConfidenceLevel.LOW
        if "confidence_reasons" in polished:
            report.confidence.reasons = polished["confidence_reasons"]
        if "blast_radius_summary" in polished:
            report.blast_radius.summary = polished["blast_radius_summary"]
        if "correlation_findings" in polished:
            report.correlation_summary = [
                CorrelatedFinding(
                    finding=c.get("finding", ""),
                    related_evidence=[],
                    source=c.get("source", "nova_formatter"),
                    severity=c.get("severity", "high"),
                    relevance_score=1.0,
                )
                for c in polished["correlation_findings"]
            ]

        print("[NovaFormatter] Report polished successfully.", flush=True)

    except Exception as exc:
        # Graceful degradation — deterministic report is always returned
        print(f"[NovaFormatter] Skipped (Nova unavailable or error: {exc})", flush=True)

    return report
