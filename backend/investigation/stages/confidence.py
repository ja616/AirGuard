from typing import List
from backend.investigation.models import RCAHypothesis, CorrelatedFinding, ConfidenceExplanation
from backend.core.constants import ConfidenceLevel

def run(rca: RCAHypothesis, findings: List[CorrelatedFinding]) -> ConfidenceExplanation:
    score = 0.5
    reasons = []
    penalties = []
    
    if not findings:
        score -= 0.2
        penalties.append("No correlated findings to support hypothesis")
    
    sources = set()
    for f in findings:
        sources.add(f.source)
        if f.severity == "high":
            score += 0.2
            reasons.append(f"Strong evidence from {f.source}")
        elif f.severity == "medium":
            score += 0.1
            reasons.append(f"Moderate evidence from {f.source}")
        else:
            score += 0.05
            
    if len(sources) > 1:
        score += 0.15
        reasons.append("Cross-system correlation found")
    elif len(sources) == 1:
        score -= 0.05
        penalties.append("Evidence limited to a single source")
        
    score = round(min(max(score, 0.0), 1.0), 2)
    
    if score >= 0.8:
        level = ConfidenceLevel.HIGH
    elif score >= 0.5:
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW
        
    return ConfidenceExplanation(score=score, level=level, reasons=reasons, penalties=penalties)
