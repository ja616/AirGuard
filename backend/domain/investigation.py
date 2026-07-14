from pydantic import BaseModel, Field, computed_field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from enum import Enum
from backend.investigation.models import OperationalReport

class InvestigationState(str, Enum):
    QUEUED = "Queued"
    STARTING = "Starting"
    COLLECTING_EVIDENCE = "CollectingEvidence"
    NORMALIZING_EVIDENCE = "NormalizingEvidence"
    CORRELATING = "Correlating"
    GENERATING_TIMELINE = "GeneratingTimeline"
    GENERATING_REPORT = "GeneratingReport"
    SLACK_DISPATCH = "SlackDispatch"
    WAITING_APPROVAL = "WaitingApproval"
    COMPLETED = "Completed"
    FAILED = "Failed"

class InvestigationMetadata(BaseModel):
    started_by: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    airflow_environment: str = "production"
    aws_account: str = "default"
    engine_version: str = "1.0.0"
    investigation_version: str = "1.0.0"

class ArtifactBase(BaseModel):
    id: str
    type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TimelineArtifact(ArtifactBase):
    type: str = "timeline"
    events: List[Dict[str, Any]]

class ReportArtifact(ArtifactBase):
    type: str = "report"
    content: OperationalReport

class GraphArtifact(ArtifactBase):
    type: str = "graph"
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

ArtifactType = Union[TimelineArtifact, ReportArtifact, GraphArtifact]

class Investigation(BaseModel):
    id: str
    state: InvestigationState = InvestigationState.QUEUED
    progress: int = 0
    metadata: InvestigationMetadata
    artifacts: List[ArtifactType] = Field(default_factory=list)
