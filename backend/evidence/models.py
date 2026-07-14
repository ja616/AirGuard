"""
First-class domain objects for Investigation Evidence.
Tools no longer return raw data; they return strongly typed Evidence.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict
from datetime import datetime
import uuid

class Evidence(BaseModel):
    """Base class for all deterministic evidence."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for this evidence graph node")
    source: str = Field(description="The deterministic tool or system that generated this")
    timestamp: datetime = Field(description="When the underlying event occurred (NOT when it was queried)")
    reliability: float = Field(ge=0.0, le=1.0, description="Inherent trustworthiness of the source (e.g., DB=1.0, Logs=0.8)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this specific payload's relevance")
    raw_payload: Dict[str, Any] = Field(description="Unmodified API/DB response for auditing")
    normalized_payload: Dict[str, Any] = Field(description="Flattened schema for the Correlation Engine")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Tags, ARNs, tracing IDs")

# --- Specific Evidence Types ---

class WorkflowEvidence(Evidence):
    dag_id: str
    run_id: str
    state: str

class TaskEvidence(Evidence):
    dag_id: str
    task_id: str
    execution_date: str
    state: str

class RetryEvidence(Evidence):
    task_id: str
    try_number: int
    exception_preview: str

class MetricEvidence(Evidence):
    metric_name: str
    value: float
    unit: str

class CloudTrailEvidence(Evidence):
    event_name: str
    user_identity: str
    resource_arn: str

class CostEvidence(Evidence):
    granularity: str
    amount: float
    currency: str

class DependencyEvidence(Evidence):
    upstream_task_id: str
    downstream_task_id: str
    relationship_type: str

class ScheduleEvidence(Evidence):
    previous_schedule: str
    new_schedule: str
