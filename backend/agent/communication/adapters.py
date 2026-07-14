from backend.investigation.models import OperationalReport

class CommunicationAdapters:
    """
    Transforms the frozen OperationalReport into various platform-native formats.
    Ensures every investigation is perfectly exportable.
    """
    
    @staticmethod
    def to_slack_blocks(report: OperationalReport) -> dict:
        """Formats the report into a Slack Block Kit payload."""
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "AirGuard Incident Report \U0001f6a8"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Root Cause:*\n{report.root_cause}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Confidence:*\n{report.confidence.value if hasattr(report.confidence, 'value') else report.confidence}"
                    }
                }
            ]
        }

    @staticmethod
    def to_jira_issue(report: OperationalReport) -> dict:
        """Formats the report into a Jira Issue creation payload."""
        return {
            "fields": {
                "project": {"key": "OPS"},
                "summary": f"[AirGuard] Automated Incident Report: {report.root_cause[:50]}",
                "description": f"Root Cause: {report.root_cause}\nTimeline Nodes: {len(report.timeline)}\n",
                "issuetype": {"name": "Bug"}
            }
        }

    @staticmethod
    def to_rest_json(report: OperationalReport) -> str:
        """Formats the report for standard REST API consumption."""
        return report.model_dump_json(indent=2)
        
    @staticmethod
    def to_markdown(report: OperationalReport) -> str:
        """Formats the report into standard Markdown for dashboards or wikis."""
        return f"""# AirGuard Incident Report
        
## Root Cause
{report.root_cause}

## Confidence
{report.confidence.value if hasattr(report.confidence, 'value') else report.confidence}

## Timeline Events
{len(report.timeline)} events recorded in the execution graph.
"""
