"""
Strongly typed models for the deterministic investigation pipeline.
Now culminates in a comprehensive Operational Report.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from backend.taxonomy.models import IncidentDefinition
from backend.core.constants import ConfidenceLevel
from backend.evidence.models import Evidence

class InvestigationRequest(BaseModel):
    dag_id: str
    task_id: Optional[str] = None
    execution_date: str
    reported_symptom: str = Field(description="The observed issue triggering this request")

class ClassifiedIncident(BaseModel):
    request: InvestigationRequest
    definition: IncidentDefinition
    
class CollectedEvidence(BaseModel):
    source: str
    raw_data: Dict[str, Any]
    
class NormalizedEvidence(BaseModel):
    standardized_format: Dict[str, Any]
    
class EvidenceGraph(BaseModel):
    nodes: List[str]
    edges: List[str]
    
class CorrelatedFinding(BaseModel):
    finding: str
    related_evidence: List[str]
    
class Timeline(BaseModel):
    events: List[Dict[str, Any]]
    
class RCAHypothesis(BaseModel):
    root_cause: str
    
class ConfidenceExplanation(BaseModel):
    """
    Replaces the naked confidence float.
    Every score must explicitly justify itself via facts.
    """
    score: float = Field(ge=0.0, le=1.0)
    level: ConfidenceLevel
    reasons: List[str] = Field(description="Positive evidence supporting the conclusion")
    penalties: List[str] = Field(description="Missing evidence or contradictory facts reducing confidence")
    
class RecommendedAction(BaseModel):
    action: str
    
class BlastRadius(BaseModel):
    """
    Structured assessment of the incident's impact scope.
    """
    affected_workflows: List[str]
    affected_tasks: List[str]
    affected_aws_resources: List[str]
    estimated_cost_impact: Optional[float] = None

class OperationalReport(BaseModel):
    """
    The final output of the Investigation Pipeline.
    A complete, structured report suitable for human SRE review.
    """
    executive_summary: str
    incident_classification: str
    timeline: Timeline
    evidence_summary: List[str]
    correlation_summary: List[CorrelatedFinding]
    blast_radius: BlastRadius
    root_cause: str
    confidence: ConfidenceExplanation
    recommendations: List[RecommendedAction]
    suggested_next_steps: List[str]
    evidence_appendix: List[Dict[str, Any]] # Raw Evidence representations
