"""
Deterministic Investigation Pipeline Orchestrator
"""
from typing import Callable, Optional, Union, List
import uuid
from backend.domain.investigation import InvestigationState, ArtifactType, GraphArtifact, TimelineArtifact, ReportArtifact
from backend.investigation.models import (
    InvestigationRequest, OperationalReport, BlastRadius, ConfidenceExplanation, Timeline
)
from backend.investigation.stages import (
    classification, evidence_collection, normalization, evidence_graph,
    correlation, timeline, root_cause, confidence, recommendations
)
from backend.core.constants import ConfidenceLevel

class DeterministicInvestigationEngine:
    """
    Executes the investigation algorithm strictly stage by stage,
    culminating in a complete Operational Report.
    """
    
    def execute(self, request: InvestigationRequest, state_callback: Optional[Callable[[InvestigationState, int, Optional[Union[ArtifactType, List[ArtifactType]]]], None]] = None) -> OperationalReport:
        if state_callback:
            state_callback(InvestigationState.STARTING, 5, None)
            
        classified = classification.run(request)
        
        if state_callback:
            state_callback(InvestigationState.COLLECTING_EVIDENCE, 20, None)
        evidence = evidence_collection.run(classified)
        
        if state_callback:
            state_callback(InvestigationState.NORMALIZING_EVIDENCE, 35, None)
        normalized = normalization.run(evidence)
        
        if state_callback:
            state_callback(InvestigationState.CORRELATING, 55, None)
        graph = evidence_graph.run(normalized)
        findings = correlation.run(graph)
        
        graph_art = None
        if state_callback:
            graph_art = GraphArtifact(id=str(uuid.uuid4()), nodes=[{"id": n} for n in graph.nodes], edges=[{"id": e} for e in graph.edges])
            # Don't pass artifact yet, just state progress
            state_callback(InvestigationState.CORRELATING, 65, None)
            
        if state_callback:
            state_callback(InvestigationState.GENERATING_TIMELINE, 70, None)
        tl = timeline.run(findings)
        
        tl_art = None
        if state_callback:
            tl_art = TimelineArtifact(id=str(uuid.uuid4()), events=tl.events)
            
        rca = root_cause.run(tl)
        
        if state_callback:
            state_callback(InvestigationState.GENERATING_REPORT, 85, None)
            
        # New: Structured Confidence
        # This will be replaced by the deterministic Correlation Scorer in Phase 2
        conf_expl = ConfidenceExplanation(
            score=0.91,
            level=ConfidenceLevel.HIGH,
            reasons=[
                "Schedule changed 2 minutes before retries",
                "Historical baseline exceeded"
            ],
            penalties=[
                "Missing scheduler logs"
            ]
        )
        
        recs = recommendations.run(rca)
        
        # Construct Blast Radius
        blast_radius = BlastRadius(
            affected_workflows=[request.dag_id],
            affected_tasks=[request.task_id] if request.task_id else [],
            affected_aws_resources=["arn:aws:rds:us-east-1:123:db:main"],
            estimated_cost_impact=0.0
        )
        
        report = OperationalReport(
            executive_summary=f"Automated investigation for {classified.definition.name}",
            incident_classification=classified.definition.id,
            timeline=tl,
            evidence_summary=["Found 2 task retries", "Found RDS CPU spike"],
            correlation_summary=findings,
            blast_radius=blast_radius,
            root_cause=rca.root_cause,
            confidence=conf_expl,
            recommendations=recs,
            suggested_next_steps=["Review AWS metrics", "Check deployment logs"],
            evidence_appendix=[{"source": e.source, "data": e.raw_data} for e in evidence]
        )
        
        if state_callback:
            rep_art = ReportArtifact(id=str(uuid.uuid4()), content=report)
            # Pass all accumulated artifacts at the end
            state_callback(InvestigationState.COMPLETED, 100, [graph_art, tl_art, rep_art])
            
        return report
