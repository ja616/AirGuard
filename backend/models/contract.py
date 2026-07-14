"""
Output Contract Models for AirGuard.
These models represent the strict data contract returned by every investigation.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class IncidentType(str, Enum):
    SCHEDULE_ANOMALY = "schedule_anomaly"
    RETRY_STORM = "retry_storm"
    TASK_FAILURE = "task_failure"
    DEPENDENCY_FAILURE = "dependency_failure"
    PERFORMANCE_REGRESSION = "performance_regression"
    COST_ANOMALY = "cost_anomaly"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ResourceDetail(BaseModel):
    service: str = Field(description="e.g., 's3', 'lambda', 'sagemaker'")
    identifier: str = Field(description="ARN or resource ID")
    status: Optional[str] = None


class TimelineEvent(BaseModel):
    timestamp: datetime
    description: str
    source: str = Field(description="Where this event was observed (e.g., CloudTrail, Airflow logs)")


class Evidence(BaseModel):
    source: str
    content: Dict[str, Any]
    relevance_score: float = Field(ge=0.0, le=1.0)


class Recommendation(BaseModel):
    action: str
    impact: str
    difficulty: str


class InvestigationResult(BaseModel):
    """
    The canonical Output Contract returned by every investigation.
    """
    incident_type: IncidentType
    dag: str = Field(description="Airflow DAG ID")
    task: Optional[str] = Field(None, description="Airflow Task ID, if applicable")
    resources: List[ResourceDetail]
    timeline: List[TimelineEvent]
    evidence: List[Evidence]
    root_cause: str = Field(description="Human-readable root cause explanation")
    confidence: ConfidenceLevel
    recommendations: List[Recommendation]
