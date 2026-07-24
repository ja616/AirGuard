"""
Deterministic Investigation Pipeline Orchestrator
==================================================
Runs each investigation stage in strict sequence. Every stage communicates
only through the model objects defined in backend/investigation/models.py
and backend/evidence/models.py — no stage imports another stage directly.

Stage execution order:
    1. evidence_validation  — check coverage against plan
    2. normalization        — signals dict from raw evidence
    3. classification       — incident type from signals
    4. evidence_graph       — correlation graph nodes/edges
    5. correlation          — correlated findings from graph + signals
    6. timeline             — chronological event list
    7. root_cause           — RCA hypothesis from findings
    8. confidence           — confidence score + reasons
    9. recommendations      — action list from signals
   10. nova_formatter       — (optional) LLM polish for human-facing fields

The Nova Formatter (step 10) is intentionally optional: the engine produces
a fully valid OperationalReport without it. If Bedrock is unreachable the
unpolished report is returned unchanged.
"""
from __future__ import annotations
from typing import Callable, Optional, Union, List, Any
import uuid

from backend.domain.investigation import (
    InvestigationState, ArtifactType,
    GraphArtifact, TimelineArtifact, ReportArtifact, EvidenceArtifact,
)
from backend.investigation.models import (
    InvestigationRequest, OperationalReport, BlastRadius, Timeline,
)
from backend.investigation.stages import (
    classification,
    normalization,
    evidence_graph,
    correlation,
    timeline,
    root_cause,
    confidence,
    recommendations,
    nova_formatter,
)
from backend.investigation.stages import evidence_validation


class DeterministicInvestigationEngine:
    """
    Executes the investigation algorithm strictly stage by stage,
    culminating in a complete OperationalReport.

    Each stage:
      - receives only model objects (no infrastructure dependencies)
      - returns only model objects
      - has no knowledge of the stages before or after it
    """

    def execute_with_evidence(
        self,
        request: InvestigationRequest,
        plan: Any,
        evidence_result: Any,
        state_callback: Optional[
            Callable[
                [InvestigationState, int, Optional[Union[ArtifactType, List[ArtifactType]]]],
                None,
            ]
        ] = None,
    ) -> OperationalReport:
        evidence = evidence_result.evidence

        # ── Stage 1 & 2: Validate + Normalize ───────────────────────────────
        validation_report = evidence_validation.run(plan, evidence)
        bundle = normalization.run(evidence)
        bundle.signals["evidence_validation"] = validation_report

        # ── Stage 3: Classify ────────────────────────────────────────────────
        classified = classification.run(request, bundle)

        # ── Stage 4 & 5: Graph + Correlate ──────────────────────────────────
        if state_callback:
            state_callback(InvestigationState.CORRELATING, 55, None)

        graph = evidence_graph.run(bundle, evidence)
        findings = correlation.run(graph, bundle)

        graph_art = None
        if state_callback:
            graph_art = GraphArtifact(
                id=str(uuid.uuid4()),
                nodes=[n.model_dump() for n in graph.nodes],
                edges=[e.model_dump() for e in graph.edges],
            )

        # ── Stage 6: Timeline ────────────────────────────────────────────────
        if state_callback:
            state_callback(InvestigationState.GENERATING_TIMELINE, 70, None)

        tl = timeline.run(evidence, findings)
        tl_art = None
        if state_callback:
            tl_art = TimelineArtifact(id=str(uuid.uuid4()), events=tl.events)

        # ── Stage 7-9: RCA, Confidence, Recommendations ─────────────────────
        rca = root_cause.run(tl, classified, findings)
        conf_expl = confidence.run(classified, findings, bundle, plan=plan)
        recs = recommendations.run(classified, bundle)

        # ── Assemble Blast Radius ────────────────────────────────────────────
        blast_radius = BlastRadius(
            affected_workflows=[request.dag_id],
            affected_tasks=[request.task_id] if request.task_id else [],
            affected_aws_resources=[],
            estimated_cost_impact=0.0,
        )

        # ── Build initial executive summary from structured context ──────────
        ctx = request.incident_context
        if ctx and ctx.failed_node_id:
            retry_str = f" after {ctx.retry_number} retries" if ctx.retry_number else ""
            initial_summary = (
                f"Task '{ctx.failed_node_id}' in workflow '{ctx.workflow_id}' failed"
                f"{retry_str} (state: {ctx.execution_state or 'failed'}, env: {ctx.environment}). "
                f"Investigation goal: {ctx.investigation_goal.value}. "
                f"Classification: {classified.definition.name}."
            )
        elif ctx:
            initial_summary = (
                f"Workflow '{ctx.workflow_id}' reported a '{ctx.execution_state or 'failure'}' "
                f"incident in {ctx.environment}. Classification: {classified.definition.name}."
            )
        else:
            initial_summary = (
                f"Investigation for {classified.definition.name}: "
                f"{request.reported_symptom or request.dag_id}."
            )

        # ── Assemble OperationalReport ───────────────────────────────────────
        if state_callback:
            state_callback(InvestigationState.GENERATING_REPORT, 85, None)

        report = OperationalReport(
            executive_summary=initial_summary,
            incident_classification=classified.definition.id,
            timeline=tl,
            evidence_summary=[f"{k}: {v}" for k, v in bundle.signals.items()],
            correlation_summary=findings,
            blast_radius=blast_radius,
            root_cause=rca.root_cause,
            confidence=conf_expl,
            recommendations=recs,
            suggested_next_steps=[a.action for a in recs],
            evidence_appendix=[e.model_dump() for e in evidence],
        )

        # ── Stage 10: Nova Formatter (optional presentation layer) ───────────
        report = nova_formatter.run(report, evidence)

        # ── Emit artifacts ───────────────────────────────────────────────────
        if state_callback:
            rep_art = ReportArtifact(id=str(uuid.uuid4()), content=report)
            ev_art = EvidenceArtifact(
                id=str(uuid.uuid4()),
                collected=[e.model_dump() for e in evidence],
            )
            state_callback(
                InvestigationState.GENERATING_REPORT, 90,
                [graph_art, tl_art, rep_art, ev_art],
            )

        return report
