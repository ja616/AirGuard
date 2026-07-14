import uuid
from typing import Dict, Any
from backend.domain.evidence import CloudWatchEvidence, CloudTrailEvidence

def map_cloudwatch_to_evidence(metric_name: str, raw_response: Dict[str, Any]) -> CloudWatchEvidence:
    """Strict mapping from raw CloudWatch dict to Evidence model."""
    results = raw_response.get("MetricDataResults", [])
    datapoints = []
    if results:
        timestamps = results[0].get("Timestamps", [])
        values = results[0].get("Values", [])
        for t, v in zip(timestamps, values):
            datapoints.append({"timestamp": str(t), "value": v})
            
    return CloudWatchEvidence(
        id=str(uuid.uuid4()),
        metric_name=metric_name,
        datapoints=datapoints,
        payload=raw_response
    )

def map_cloudtrail_to_evidence(raw_event: Dict[str, Any]) -> CloudTrailEvidence:
    """Strict mapping from raw CloudTrail dict to Evidence model."""
    return CloudTrailEvidence(
        id=str(uuid.uuid4()),
        event_name=raw_event.get("EventName", "unknown"),
        username=raw_event.get("Username", "unknown"),
        payload=raw_event
    )
