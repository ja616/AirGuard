"""
Strongly typed, immutable Pydantic models for the Correlation Engine.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from backend.evidence.models import Evidence

class ConfidenceScore(BaseModel):
    """Deterministic score with required justification."""
    score: float = Field(ge=0.0, le=1.0)
    reason: str = Field(description="Deterministic rule that granted this score")
    penalties: List[str] = Field(default_factory=list, description="Rules that deducted from this score")

class GraphNode(BaseModel):
    """A node in the evidence graph, encapsulating exactly one Evidence object."""
    id: str
    evidence: Evidence

class GraphEdge(BaseModel):
    """A directed edge representing a deterministic relationship between evidence."""
    source_node_id: str
    target_node_id: str
    relationship_type: str = Field(description="e.g., Triggered, Depends On, Caused, Executed, Modified, Observed")
    confidence: ConfidenceScore
    timestamp: datetime

class InvestigationGraph(BaseModel):
    """The central internal graph representation."""
    nodes: Dict[str, GraphNode] = Field(default_factory=dict)
    edges: List[GraphEdge] = Field(default_factory=list)

class TimelineEvent(BaseModel):
    """A single chronological event."""
    timestamp: datetime
    event_type: str
    description: str
    related_node_ids: List[str]

class Timeline(BaseModel):
    """Chronological reconstruction of the incident."""
    events: List[TimelineEvent] = Field(default_factory=list)

class ResourceLink(BaseModel):
    """Maps Airflow concepts to AWS resources."""
    workflow_id: str
    task_id: str
    aws_resource_arn: str
    confidence: ConfidenceScore

class CostAttribution(BaseModel):
    """Deterministic mapping of billing data to tasks."""
    responsible_workflow: str
    responsible_task: str
    estimated_cost: float
    confidence: ConfidenceScore
    evidence_used_ids: List[str]

class DependencyChain(BaseModel):
    """A sequence of task IDs representing upstream/downstream blocking."""
    path: List[str]
    critical_path: bool

class CorrelationResult(BaseModel):
    """The final output of the Correlation Engine."""
    graph: InvestigationGraph
    timeline: Timeline
    resource_links: List[ResourceLink]
    cost_attribution: Optional[CostAttribution] = None
    dependency_chains: List[DependencyChain]
