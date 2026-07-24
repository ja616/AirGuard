"""
Strongly typed models for the deterministic investigation pipeline.

Core domain is workflow-agnostic. Orchestrator-specific concepts (Airflow
dag_run_id, task_id, etc.) are mapped to generic terms in the adapter layer.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, computed_field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
import uuid
from backend.taxonomy.models import IncidentDefinition
from backend.core.constants import ConfidenceLevel
from backend.evidence.models import Evidence

from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────────────────────
# Incident Context Enums
# ─────────────────────────────────────────────────────────────────────────────

class TriggerSource(str, Enum):
    """Where the investigation trigger originated."""
    ORCHESTRATOR_CALLBACK = "orchestrator_callback"  # Airflow/Prefect/etc callback
    MANUAL = "manual"
    API = "api"
    SLACK = "slack"


class IncidentSeverity(str, Enum):
    """
    Severity controls the investigation budget (top-N capabilities),
    not domain selection.
    """
    CRITICAL = "critical"  # budget: top 10 capabilities
    HIGH = "high"          # budget: top 7
    MEDIUM = "medium"      # budget: top 5
    LOW = "low"            # budget: top 3


class InvestigationGoal(str, Enum):
    """
    First-class goal field that deterministically boosts capability scores.
    """
    ROOT_CAUSE = "root_cause"
    IMPACT_ANALYSIS = "impact_analysis"
    COST_ANALYSIS = "cost_analysis"
    PERFORMANCE = "performance"


# ─────────────────────────────────────────────────────────────────────────────
# IncidentContext — Generic, Workflow-Agnostic
# ─────────────────────────────────────────────────────────────────────────────

class IncidentContext(BaseModel):
    """
    Structured operational context for an incident.
    All fields are orchestrator-agnostic. Airflow-specific concepts are mapped
    by the adapter in backend/integrations/airflow/incident_adapter.py.

    Mapping reference (Airflow → generic):
        dag_id          → workflow_id
        dag_run_id      → workflow_execution_id
        task_id         → failed_node_id
        state           → execution_state
        try_number      → retry_number
        airflow_error   → orchestrator_error_type
    """
    # Workflow identity
    workflow_id: str = Field(description="The workflow being investigated (e.g. dag_id)")
    workflow_execution_id: Optional[str] = Field(
        default=None,
        description="The specific execution/run to pin the investigation to"
    )
    failed_node_id: Optional[str] = Field(
        default=None,
        description="The specific node/task that first failed"
    )
    execution_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the failure occurred"
    )

    # Incident metadata
    severity: IncidentSeverity = Field(
        default=IncidentSeverity.MEDIUM,
        description="Controls the investigation budget (top-N capabilities)"
    )
    trigger_source: TriggerSource = Field(
        default=TriggerSource.API,
        description="What originated this investigation"
    )
    environment: Literal["dev", "staging", "prod"] = Field(
        default="prod",
        description="Deployment environment — influences priority and reporting"
    )
    investigation_goal: InvestigationGoal = Field(
        default=InvestigationGoal.ROOT_CAUSE,
        description="Primary investigation objective — deterministically boosts capability scores"
    )

    # Generic execution state (no orchestrator-specific types)
    execution_state: Optional[str] = Field(
        default=None,
        description="e.g. 'failed', 'upstream_failed', 'zombie'"
    )
    retry_number: Optional[int] = Field(
        default=None,
        description="Number of retries already attempted"
    )
    orchestrator_error_type: Optional[str] = Field(
        default=None,
        description="Generic error type string from the orchestrator"
    )

    # Escape hatch
    additional_context: Dict[str, str] = Field(
        default_factory=dict,
        description="Extra key-value metadata from the trigger source"
    )

    def derive_symptom(self) -> str:
        """
        Auto-generates a human-readable reported_symptom string from structured
        context. Used internally by pipeline stages that still expect a text description.
        """
        parts = [f"Workflow '{self.workflow_id}'"]
        if self.failed_node_id:
            retry_str = f", attempt {self.retry_number}" if self.retry_number else ""
            parts.append(f"node '{self.failed_node_id}' failed (state: {self.execution_state or 'failed'}{retry_str})")
        elif self.execution_state:
            parts.append(f"reached state '{self.execution_state}'")
        else:
            parts.append("reported an incident")
        parts.append(f"[{self.severity.value}/{self.environment}]")
        parts.append(f"via {self.trigger_source.value}")
        return " — ".join(parts)


class InvestigationRequest(BaseModel):
    """
    The internal investigation request. Accepts either:
      - A structured IncidentContext (new path — from Airflow callbacks, API, etc.)
      - Legacy dag_id + reported_symptom strings (old path — still supported)

    All internal pipeline stages read dag_id, task_id, and reported_symptom.
    These are derived from IncidentContext when present.
    """
    investigation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # ── NEW: Structured incident context (primary input path) ──────────────
    incident_context: Optional[IncidentContext] = Field(
        default=None,
        description="Structured operational context. When set, all other fields are derived."
    )

    # ── LEGACY/DERIVED: Internal pipeline fields ────────────────────────────
    # These are populated from incident_context if provided, or can be set directly.
    dag_id: str = Field(default="", description="Derived from incident_context.workflow_id")
    task_id: Optional[str] = Field(default=None, description="Derived from incident_context.failed_node_id")
    execution_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reported_symptom: str = Field(
        default="",
        description="Auto-derived from incident_context.derive_symptom() when context is provided"
    )
    environment: str = Field(default="production")
    time_window: Optional[int] = Field(default=3600, description="Time window in seconds")
    priority: str = Field(default="medium")
    user_context: Optional[str] = None
    manual_hints: List[str] = Field(default_factory=list)
    requested_services: List[str] = Field(default_factory=list)
    optional_tags: Dict[str, str] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """Derive legacy fields from IncidentContext when present."""
        ctx = self.incident_context
        if ctx:
            object.__setattr__(self, "dag_id", ctx.workflow_id)
            object.__setattr__(self, "task_id", ctx.failed_node_id)
            object.__setattr__(self, "execution_date", ctx.execution_timestamp.isoformat())
            object.__setattr__(self, "reported_symptom", ctx.derive_symptom())
            object.__setattr__(self, "environment", ctx.environment)
            object.__setattr__(self, "priority", ctx.severity.value)

    @classmethod
    def from_context(cls, investigation_id: str, ctx: IncidentContext) -> "InvestigationRequest":
        """Factory: create a request from a structured IncidentContext."""
        return cls(investigation_id=investigation_id, incident_context=ctx)

    @classmethod
    def from_legacy(cls, investigation_id: str, dag_id: str, user_query: str) -> "InvestigationRequest":
        """
        Factory: create a request from a legacy dag_id + user_query string.
        Wraps the query in a minimal IncidentContext for uniform planner handling.
        """
        ctx = IncidentContext(
            workflow_id=dag_id,
            execution_state="unknown",
            trigger_source=TriggerSource.MANUAL,
            additional_context={"user_query": user_query}
        )
        # Override symptom with the user's original text for keyword scoring
        req = cls(investigation_id=investigation_id, incident_context=ctx)
        object.__setattr__(req, "reported_symptom", user_query)
        return req



class ClassifiedIncident(BaseModel):
    request: InvestigationRequest
    definition: IncidentDefinition
    classification_confidence: float = Field(default=1.0)
    secondary_definition: Optional[IncidentDefinition] = None
    secondary_confidence: Optional[float] = None
    supporting_factors: List[str] = Field(default_factory=list)
    rejected_classes: List[str] = Field(default_factory=list)
    
class CollectedEvidence(BaseModel):
    source: str
    raw_data: Dict[str, Any]
    
class NormalizedEvidence(BaseModel):
    standardized_format: Dict[str, Any]

class NormalizedEvidenceBundle(BaseModel):
    signals: Dict[str, Any] = Field(description="Flattened signals for the voting classifier")
    evidence_ids: List[str] = Field(description="UUIDs of the raw evidence items used")
    source_count: int = Field(description="Number of distinct sources contributing to the bundle")
    
class GraphNode(BaseModel):
    id: str
    title: str
    subtitle: str
    severity: str
    source: str
    icon: str
    
class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: str

class EvidenceGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    
class CorrelatedFinding(BaseModel):
    finding: str
    related_evidence: List[str]
    source: str = Field(default="orchestrator")
    severity: str = Field(default="medium")
    relevance_score: float = Field(default=1.0)
    
class Timeline(BaseModel):
    events: List[Dict[str, Any]]
    
class RCAHypothesis(BaseModel):
    root_cause: str
    contributing_factors: List[str] = Field(default_factory=list)
    certainty: float = Field(default=1.0)
    
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
    summary: List[str] = Field(default_factory=list, description="LLM-generated operational bullet points")

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
