from typing import List
from backend.investigation.models import NormalizedEvidence, EvidenceGraph

def run(normalized: List[NormalizedEvidence]) -> EvidenceGraph:
    # Build deterministic relationship graph
    return EvidenceGraph(nodes=["task", "rds"], edges=["task_depends_on_rds"])
