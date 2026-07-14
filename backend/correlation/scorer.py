"""
Deterministic Confidence Aggregation.
"""
from backend.correlation.models import InvestigationGraph
from backend.investigation.models import ConfidenceExplanation
from backend.core.constants import ConfidenceLevel

class CorrelationScorer:
    """
    Traverses the fully correlated InvestigationGraph and aggregates the 
    individual edge confidences into a single, explainable Incident Confidence.
    """
    @staticmethod
    def score_incident(graph: InvestigationGraph) -> ConfidenceExplanation:
        if not graph.edges:
            return ConfidenceExplanation(
                score=0.0,
                level=ConfidenceLevel.LOW,
                reasons=[],
                penalties=["No correlated edges found in the graph."]
            )
            
        total_score = 0.0
        reasons = set()
        penalties = set()
        
        for edge in graph.edges:
            total_score += edge.confidence.score
            
            # Aggregate reasons and penalties
            reasons.add(f"[{edge.relationship_type}] {edge.confidence.reason}")
            for penalty in edge.confidence.penalties:
                penalties.add(f"[{edge.relationship_type}] Penalty: {penalty}")
                
        # Simple unweighted average for now (can be expanded via BlastRadiusRules later)
        avg_score = total_score / len(graph.edges)
        
        # Map average score to discrete level
        level = ConfidenceLevel.LOW
        if avg_score >= 0.8:
            level = ConfidenceLevel.HIGH
        elif avg_score >= 0.5:
            level = ConfidenceLevel.MEDIUM
            
        return ConfidenceExplanation(
            score=round(avg_score, 2),
            level=level,
            reasons=list(reasons),
            penalties=list(penalties)
        )
