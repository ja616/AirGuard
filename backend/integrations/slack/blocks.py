"""
Slack notification formatters — AirGuard
=========================================
All Slack message content is built here. No other module should construct
Slack message strings or emoji sequences.

Functions:
    format_investigation_complete(report, investigation_id, context) -> str
        Plain-text fallback message for post_message().
    create_investigation_blocks(report, investigation_id, context) -> List[dict]
        Block Kit rich message for send_report_blocks().
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Severity helpers
# ─────────────────────────────────────────────────────────────────────────────

_SEV_EMOJI: Dict[str, str] = {
    "CRITICAL": "🔴",
    "HIGH":     "🟠",
    "MEDIUM":   "🟡",
    "LOW":      "🟢",
}


def _sev_emoji(severity: str) -> str:
    return _SEV_EMOJI.get(severity.upper(), "✅")


# ─────────────────────────────────────────────────────────────────────────────
# Plain-text formatter (used when Block Kit is not available)
# ─────────────────────────────────────────────────────────────────────────────

def format_investigation_complete(
    report,
    investigation_id: str,
    context=None,    # Optional IncidentContext
) -> str:
    """
    Build a plain-text Slack message for a completed investigation.
    Works for both legacy (no context) and structured (with context) paths.
    """
    if context is not None:
        sev = context.severity.value.upper()
        env = context.environment
        emoji = _sev_emoji(sev)
        node_info = (
            f"\n*Failed Node:* `{context.failed_node_id}`"
            if context.failed_node_id else ""
        )
        retry_info = (
            f" (attempt {context.retry_number})"
            if context.retry_number else ""
        )
        return (
            f"{emoji} *[{sev}/{env}] Investigation Completed*\n"
            f"*Workflow:* `{context.workflow_id}`{node_info}{retry_info}\n"
            f"*Root Cause:* {report.root_cause}\n"
            f"*ID:* `{investigation_id}` | "
            f"Triggered by: {context.trigger_source.value}"
        )
    else:
        # Legacy path — no IncidentContext available
        return (
            f"✅ *Investigation Completed*\n"
            f"*ID:* `{investigation_id}`\n"
            f"*Root Cause:* {report.root_cause}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Block Kit formatters (existing + new investigation-complete block)
# ─────────────────────────────────────────────────────────────────────────────

def create_report_blocks(
    report_title: str, summary: str, status: str
) -> List[Dict[str, Any]]:
    """Generates Slack Block Kit UI for an Investigation Report."""
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"🚨 {report_title}"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Status:*\n{status}"},
                {"type": "mrkdwn", "text": f"*Summary:*\n{summary}"},
            ],
        },
        {"type": "divider"},
    ]


def create_approval_blocks(
    action_description: str, investigation_id: str
) -> List[Dict[str, Any]]:
    """Generates Slack Block Kit UI with interactive approval buttons."""
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Approval Required:*\n{action_description}",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "style": "primary",
                    "value": f"approve_{investigation_id}",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject"},
                    "style": "danger",
                    "value": f"reject_{investigation_id}",
                },
            ],
        },
    ]
