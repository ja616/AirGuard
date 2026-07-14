import uuid
from typing import Dict, Any
from backend.domain.evidence import SlackMessageEvidence

def map_slack_response_to_evidence(raw_response: Dict[str, Any]) -> SlackMessageEvidence:
    """Strict mapping from raw Slack API JSON to Evidence model."""
    return SlackMessageEvidence(
        id=str(uuid.uuid4()),
        channel=raw_response.get("channel", "unknown"),
        ts=raw_response.get("ts", "unknown"),
        payload=raw_response
    )
