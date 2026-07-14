from backend.investigation.models import EvidenceGraph, CorrelatedFinding

def run(graph: EvidenceGraph) -> list[CorrelatedFinding]:
    # Identify relationships and anomalies
    return [
        CorrelatedFinding(finding="Spike in RDS connections correlates with task retries", related_evidence=["task_depends_on_rds"])
    ]
