import time
import boto3
from typing import Dict, Any, List
from backend.integrations.core.interfaces import ICloudWatchClient
from backend.integrations.core.retry import with_retry
from backend.integrations.core.telemetry import with_telemetry
from backend.integrations.core.config import config

class Boto3CloudWatchClient(ICloudWatchClient):
    def __init__(self):
        self.client = boto3.client('cloudwatch', region_name=config.aws_region)

    @with_telemetry("AWS_CloudWatch", "health")
    def health(self) -> bool:
        try:
            self.client.list_metrics(Namespace='AWS/EC2')
            return True
        except Exception:
            return False

    def ping(self) -> float:
        start = time.time()
        self.health()
        return (time.time() - start) * 1000

    def capabilities(self) -> List[str]:
        return ["metrics", "alarms"]

    @with_retry(max_retries=5, initial_backoff=1.0, max_backoff=16.0)
    @with_telemetry("AWS_CloudWatch", "get_metric_data")
    def get_metric_data(self, queries: List[Dict[str, Any]], start_time: Any, end_time: Any) -> Dict[str, Any]:
        return self.client.get_metric_data(
            MetricDataQueries=queries,
            StartTime=start_time,
            EndTime=end_time
        )
