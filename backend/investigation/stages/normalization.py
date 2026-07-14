from typing import List
from backend.investigation.models import CollectedEvidence, NormalizedEvidence

def run(evidence: List[CollectedEvidence]) -> List[NormalizedEvidence]:
    # Deterministically structure evidence
    return [
        NormalizedEvidence(standardized_format={"metric": e.source, "value": e.raw_data})
        for e in evidence
    ]
