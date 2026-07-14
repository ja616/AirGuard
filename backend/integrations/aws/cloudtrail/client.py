import time
import boto3
from typing import Dict, Any, List
from backend.integrations.core.interfaces import ICloudTrailClient
from backend.integrations.core.retry import with_retry
from backend.integrations.core.telemetry import with_telemetry
from backend.integrations.core.config import config

class Boto3CloudTrailClient(ICloudTrailClient):
    def __init__(self):
        self.client = boto3.client('cloudtrail', region_name=config.aws_region)

    @with_telemetry("AWS_CloudTrail", "health")
    def health(self) -> bool:
        try:
            self.client.describe_trails()
            return True
        except Exception:
            return False

    def ping(self) -> float:
        start = time.time()
        self.health()
        return (time.time() - start) * 1000

    def capabilities(self) -> List[str]:
        return ["events"]
        
    @with_retry(max_retries=3)
    @with_telemetry("AWS_CloudTrail", "lookup_events")
    def lookup_events(self, attributes: List[Dict[str, Any]], start_time: Any, end_time: Any) -> List[Dict[str, Any]]:
        response = self.client.lookup_events(
            LookupAttributes=attributes,
            StartTime=start_time,
            EndTime=end_time
        )
        return response.get('Events', [])
