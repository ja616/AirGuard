"""
First-class domain objects for Investigation Evidence.
Tools no longer return raw data; they return strongly typed Evidence.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List
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

class ToolFailure(BaseModel):
    tool: str
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EvidenceBundleResult(BaseModel):
    evidence: List[Evidence]
    failures: List[ToolFailure]
    collection_duration_ms: int = 0

# --- Specific Typed Evidence ---

class AirflowEvidence(Evidence):
    pass

class CloudWatchEvidence(Evidence):
    pass

class CloudTrailEvidence(Evidence):
    pass

class SchedulerEvidence(Evidence):
    pass

class SlackEvidence(Evidence):
    pass

class LambdaEvidence(Evidence):
    pass

class CostEvidence(Evidence):
    pass

class WorkerEvidence(Evidence):
    pass

class InfrastructureEvidence(Evidence):
    pass
