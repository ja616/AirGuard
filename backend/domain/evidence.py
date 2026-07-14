from pydantic import BaseModel
from typing import Dict, Any, List

class Evidence(BaseModel):
    id: str
    type: str
    source: str
    payload: Dict[str, Any]

class AirflowTaskEvidence(Evidence):
    type: str = "airflow_task"
    source: str = "airflow"
    dag_id: str
    run_id: str
    task_id: str
    state: str
    log_preview: str

class CloudWatchEvidence(Evidence):
    type: str = "cloudwatch_metric"
    source: str = "aws_cloudwatch"
    metric_name: str
    datapoints: List[Dict[str, Any]]

class CloudTrailEvidence(Evidence):
    type: str = "cloudtrail_event"
    source: str = "aws_cloudtrail"
    event_name: str
    username: str

class SlackMessageEvidence(Evidence):
    type: str = "slack_message"
    source: str = "slack"
    channel: str
    ts: str
