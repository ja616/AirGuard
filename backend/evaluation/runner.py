"""
The Evaluation Runner. Feeds synthetic evidence into the Investigation Pipeline.
"""
from backend.correlation.engine import CorrelationEngine
from backend.evaluation.synthetic_incidents.base_scenario import BaseSyntheticScenario
from backend.evaluation.models import EvaluationResult
from backend.investigation.stages import root_cause
from backend.correlation.scorer import CorrelationScorer
from backend.investigation.models import BlastRadius

class EvaluationRunner:
    """
    Orchestrates the evaluation of a scenario.
    Bypasses the real tools and feeds synthetic evidence directly into the Correlation Engine.
    """
    def __init__(self):
        self.engine = CorrelationEngine()

    def run_scenario(self, scenario: BaseSyntheticScenario) -> EvaluationResult:
        evidence = scenario.generate_evidence()
        ground_truth = scenario.get_ground_truth()
        
        # 1. Correlate Evidence
        correlation_result = self.engine.process(evidence)
        
        # 2. Extract Root Cause
        rca = root_cause.run(correlation_result.timeline)
        
        # 3. Score Incident Confidence
        confidence_expl = CorrelationScorer.score_incident(correlation_result.graph)
        
        # 4. Mock Blast Radius (would normally come from knowledge base traversal)
        blast_radius = BlastRadius(
            affected_workflows=[e.dag_id for e in evidence if hasattr(e, 'dag_id')],
            affected_tasks=[],
            affected_aws_resources=[],
            estimated_cost_impact=0.0
        )
        
        # --- Evaluate ---
        errors = []
        
        # Root Cause
        rc_match = ground_truth.expected_root_cause in rca.root_cause
        if not rc_match:
            errors.append(f"Root cause '{rca.root_cause}' did not contain expected '{ground_truth.expected_root_cause}'")
            
        # Timeline
        tl_len = len(correlation_result.timeline.events)
        tl_suff = tl_len >= ground_truth.expected_timeline_length_min
        if not tl_suff:
            errors.append(f"Timeline length {tl_len} < required {ground_truth.expected_timeline_length_min}")
            
        # Confidence
        conf_match = confidence_expl.level == ground_truth.expected_confidence_level
        if not conf_match:
            errors.append(f"Confidence {confidence_expl.level} != expected {ground_truth.expected_confidence_level}")
            
        # Blast Radius
        br_match = all(wf in blast_radius.affected_workflows for wf in ground_truth.expected_blast_radius_workflows)
        if not br_match:
            errors.append(f"Blast radius missed expected workflows: {ground_truth.expected_blast_radius_workflows}")
            
        passed = rc_match and tl_suff and conf_match and br_match
        
        return EvaluationResult(
            scenario_name=scenario.name,
            passed=passed,
            root_cause_match=rc_match,
            timeline_sufficient=tl_suff,
            confidence_calibrated=conf_match,
            blast_radius_accurate=br_match,
            actual_root_cause=rca.root_cause,
            actual_confidence_level=str(confidence_expl.level.value),
            errors=errors
        )
