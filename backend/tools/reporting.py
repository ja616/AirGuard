"""
Reporting Capability Tools.
Purpose: Present findings to external systems (Jira, Slack, Markdown).
"""
from backend.tools.decorators import deterministic_tool

@deterministic_tool(timeout=10, retries=3, required_permissions=["jira.issue.create"])
def create_jira_ticket(report_data: dict) -> str:
    """
    Purpose: Create an operational ticket containing the investigation report.
    Outputs: Jira Ticket URL
    """
    return "https://jira.internal/AIRGUARD-101"
