from typing import List, Any
from backend.investigation.models import ConfidenceExplanation, ClassifiedIncident, CorrelatedFinding, NormalizedEvidenceBundle
from backend.core.constants import ConfidenceLevel

def run(classified: ClassifiedIncident, findings: List[CorrelatedFinding], bundle: NormalizedEvidenceBundle, plan: Any = None) -> ConfidenceExplanation:
    """
    Calculates confidence based strictly on evidence corroboration.
    """
    score = 0.4 # Baseline score
    reasons = []
    penalties = []
    
    if not findings:
        penalties.append("No correlated findings were generated from the evidence.")
    else:
        # Tally high-severity and secondary findings
        high_severity_findings = [f for f in findings if f.severity.lower() in ("high", "critical")]
        other_findings = [f for f in findings if f.severity.lower() not in ("high", "critical")]
        
        if high_severity_findings:
            boost = 0.2 * len(high_severity_findings)
            score += boost
            sources = set([f.source for f in high_severity_findings])
            reasons.append(f"Strong corroboration from {len(high_severity_findings)} high-severity findings across sources: {', '.join(sources)}.")
            
        if other_findings:
            boost = 0.1 * len(other_findings)
            score += boost
            reasons.append(f"Additional corroboration from {len(other_findings)} secondary findings.")
            
        # Check cross-domain corroboration
        sources = set([f.source for f in findings])
        if len(sources) > 1:
            score += 0.1
            reasons.append("Cross-domain evidence corroboration detected (multiple distinct telemetry sources).")
            
        if len(findings) == 1 and findings[0].severity.lower() == "low":
            penalties.append("Only a single, low-severity finding supports the hypothesis.")
            score -= 0.2

    # Ensure bounds
    score = max(0.0, min(1.0, score))
    
    # Determine level
    if score >= 0.8:
        level = ConfidenceLevel.HIGH
    elif score >= 0.5:
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW
        
    return ConfidenceExplanation(
        score=round(score, 2),
        level=level,
        reasons=reasons,
        penalties=penalties
    )
