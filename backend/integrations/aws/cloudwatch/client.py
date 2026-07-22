import time
import boto3
from typing import Dict, Any, List
from backend.integrations.core.interfaces import ICloudWatchClient
from backend.integrations.core.retry import with_retry
from backend.integrations.core.telemetry import with_telemetry
from backend.integrations.core.config import config

class Boto3CloudWatchClient(ICloudWatchClient):
    def __init__(self):
        from backend.integrations.aws.client_factory import get_boto3_client
        self.client = get_boto3_client('cloudwatch')

    @with_telemetry("AWS_CloudWatch", "health")
    def health(self) -> bool:
        self.client.list_metrics(Namespace='AWS/EC2')
        return True

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

    @with_retry(max_retries=3)
    @with_telemetry("AWS_CloudWatch", "get_lambda_errors")
    def get_lambda_errors(self, function_name: str, start_time: Any, end_time: Any) -> int:
        res = self.client.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Errors',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        datapoints = res.get('Datapoints', [])
        return int(sum(dp.get('Sum', 0) for dp in datapoints))

    @with_retry(max_retries=3)
    @with_telemetry("AWS_CloudWatch", "get_lambda_duration")
    def get_lambda_duration(self, function_name: str, start_time: Any, end_time: Any) -> float:
        res = self.client.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Duration',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Maximum']
        )
        datapoints = res.get('Datapoints', [])
        if not datapoints:
            return 0.0
        return max(dp.get('Maximum', 0) for dp in datapoints)

    @with_retry(max_retries=3)
    @with_telemetry("AWS_CloudWatch", "get_sagemaker_training_metrics")
    def get_sagemaker_training_metrics(self, job_name: str, start_time: Any, end_time: Any) -> Dict[str, Any]:
        return {
            "job_name": job_name,
            "duration": 7200.0, # Simulated mock values since cost explorer isn't fully wired
            "instance_type": "ml.p4d.24xlarge"
        }
