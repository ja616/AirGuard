from typing import List, Dict, Any

def create_report_blocks(report_title: str, summary: str, status: str) -> List[Dict[str, Any]]:
    """Generates Slack Block Kit UI for an Investigation Report."""
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 {report_title}"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Status:*\n{status}"},
                {"type": "mrkdwn", "text": f"*Summary:*\n{summary}"}
            ]
        },
        {"type": "divider"}
    ]

def create_approval_blocks(action_description: str, investigation_id: str) -> List[Dict[str, Any]]:
    """Generates Slack Block Kit UI with interactive approval buttons."""
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Approval Required:*\n{action_description}"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "style": "primary",
                    "value": f"approve_{investigation_id}"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject"},
                    "style": "danger",
                    "value": f"reject_{investigation_id}"
                }
            ]
        }
    ]
