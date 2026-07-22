from typing import List
from backend.investigation.models import RCAHypothesis, Timeline, CorrelatedFinding, ClassifiedIncident

def run(timeline: Timeline, classified: ClassifiedIncident, findings: List[CorrelatedFinding]) -> RCAHypothesis:
    # 1. Derive root cause directly from the most severe and relevant evidence correlation
    root_cause = "Insufficient evidence to determine a definitive root cause."
    
    if findings:
        # Sort findings by severity (critical > high > medium > low) then by relevance_score
        severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        sorted_findings = sorted(
            findings, 
            key=lambda f: (severity_weights.get(f.severity.lower(), 0), f.relevance_score), 
            reverse=True
        )
        
        # Combine the top 1 or 2 most severe findings into a coherent root cause string
        top_findings = sorted_findings[:2]
        if len(top_findings) == 1:
            root_cause = top_findings[0].finding
        else:
            # Only combine if both are at least "high" severity, otherwise just take the primary
            if severity_weights.get(top_findings[1].severity.lower(), 0) >= 3:
                root_cause = f"{top_findings[0].finding}. Additionally, {top_findings[1].finding.lower()}."
            else:
                root_cause = top_findings[0].finding

    # 2. Extract contributing factors from the remaining findings
    factors = [f.finding for f in findings if f.finding not in root_cause]
    
    # 3. Add secondary incidents if any
    if classified.secondary_definition:
        factors.append(f"Secondary Incident Signature: {classified.secondary_definition.name}")
        
    for s in classified.supporting_factors:
        factors.append(f"Supporting Factor: {s}")
        
    # Certainty is no longer just the classification confidence, but we'll let confidence.py 
    # calculate the true detailed score later. We pass a baseline here.
    return RCAHypothesis(
        root_cause=root_cause,
        contributing_factors=factors,
        certainty=classified.classification_confidence
    )
