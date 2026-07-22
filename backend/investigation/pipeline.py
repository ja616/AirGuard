"""
Deterministic Investigation Pipeline Orchestrator
"""
from typing import Callable, Optional, Union, List, Any
import uuid
from backend.domain.investigation import InvestigationState, ArtifactType, GraphArtifact, TimelineArtifact, ReportArtifact, EvidenceArtifact
from backend.investigation.models import (
    InvestigationRequest, OperationalReport, BlastRadius, ConfidenceExplanation, Timeline
)
from backend.investigation.stages import (
    classification, normalization, evidence_graph,
    correlation, timeline, root_cause, confidence, recommendations
)
from backend.core.constants import ConfidenceLevel
from backend.replay.persistence import persist_for_replay

class DeterministicInvestigationEngine:
    """
    Executes the investigation algorithm strictly stage by stage,
    culminating in a complete Operational Report.
    """
    
    def execute_with_evidence(self, request: InvestigationRequest, plan: Any, evidence_result: Any, state_callback: Optional[Callable[[InvestigationState, int, Optional[Union[ArtifactType, List[ArtifactType]]]], None]] = None) -> OperationalReport:
        evidence = evidence_result.evidence
        
        from backend.investigation.stages import evidence_validation
        validation_report = evidence_validation.run(plan, evidence)
        bundle = normalization.run(evidence)
        bundle.signals["evidence_validation"] = validation_report
        
        # Now classify
        classified = classification.run(request, bundle)
        
        if state_callback:
            state_callback(InvestigationState.CORRELATING, 55, None)
            
        graph = evidence_graph.run(bundle, evidence)
        findings = correlation.run(graph, bundle)
        
        graph_art = None
        if state_callback:
            graph_art = GraphArtifact(id=str(uuid.uuid4()), nodes=[n.model_dump() for n in graph.nodes], edges=[e.model_dump() for e in graph.edges])
            state_callback(InvestigationState.CORRELATING, 65, None)
            
        if state_callback:
            state_callback(InvestigationState.GENERATING_TIMELINE, 70, None)
        tl = timeline.run(evidence, findings)
        
        tl_art = None
        if state_callback:
            tl_art = TimelineArtifact(id=str(uuid.uuid4()), events=tl.events)
            
        rca = root_cause.run(tl, classified, findings)
        
        if state_callback:
            state_callback(InvestigationState.GENERATING_REPORT, 85, None)
            
        # Pass plan to confidence calculation
        conf_expl = confidence.run(classified, findings, bundle, plan=plan)
        # Pass bundle to recommendations
        recs = recommendations.run(classified, bundle)
        
        blast_radius = BlastRadius(
            affected_workflows=[request.dag_id],
            affected_tasks=[request.task_id] if request.task_id else [],
            affected_aws_resources=[],
            estimated_cost_impact=0.0
        )
        
        sec_str = f" Secondary: {classified.secondary_definition.name}" if classified.secondary_definition else ""
        
        report = OperationalReport(
            executive_summary=f"Automated investigation for {classified.definition.name}{sec_str}",
            incident_classification=classified.definition.id,
            timeline=tl,
            evidence_summary=[f"{k}: {v}" for k, v in bundle.signals.items()],
            correlation_summary=findings,
            blast_radius=blast_radius,
            root_cause=rca.root_cause,
            confidence=conf_expl,
            recommendations=recs,
            suggested_next_steps=[a.action for a in recs],
            evidence_appendix=[e.model_dump() for e in evidence]
        )
        
        # Optional Nova Polish for the executive summary ONLY
        import os
        if os.environ.get("AGENTCORE_HARNESS_ID"):
            try:
                from backend.integrations.aws.client_factory import get_boto3_client
                client = get_boto3_client("bedrock-runtime")
                prompt = (
                    f"Rewrite this incident summary into a single, polished, professional executive summary paragraph:\n"
                    f"Root Cause: {report.root_cause}\n"
                    f"Confidence: {report.confidence.score * 100}%\n"
                    f"Key Next Step: {report.suggested_next_steps[0] if report.suggested_next_steps else 'Investigate'}\n"
                    f"Do not add any new facts or change the root cause."
                )
                
                response = client.invoke_model(
                    modelId="us.amazon.nova-pro-v1:0",
                    contentType="application/json",
                    accept="application/json",
                    body='{"messages": [{"role": "user", "content": [{"text": "' + prompt.replace('"', '\\"') + '"}]}]}'
                )
                import json
                response_body = json.loads(response['body'].read())
                # Nova payload structure extraction
                polished_text = response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
                if polished_text:
                    report.executive_summary = polished_text.strip()
            except Exception as e:
                print(f"[DeterministicEngine] Failed to polish executive summary with Nova: {e}")
        
        if state_callback:
            rep_art = ReportArtifact(id=str(uuid.uuid4()), content=report)
            ev_art = EvidenceArtifact(id=str(uuid.uuid4()), collected=[e.model_dump() for e in evidence])
            state_callback(InvestigationState.GENERATING_REPORT, 90, [graph_art, tl_art, rep_art, ev_art])
            
        return report
