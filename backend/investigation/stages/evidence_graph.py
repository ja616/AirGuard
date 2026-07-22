from typing import List
from backend.investigation.models import NormalizedEvidenceBundle, EvidenceGraph, GraphNode, GraphEdge
from backend.investigation.models import CollectedEvidence

def run(bundle: NormalizedEvidenceBundle, raw_evidence: List[CollectedEvidence]) -> EvidenceGraph:
    nodes = []
    edges = []
    
    # Map evidence to rich nodes
    evidence_map = {e.source: e for e in raw_evidence}
    
    for idx, e in enumerate(raw_evidence):
        icon = "Database" if "postgres" in e.source.lower() or "airflow" in e.source.lower() else "Cloud"
        severity = "High" if "fail" in str(e.raw_payload).lower() or "error" in str(e.raw_payload).lower() else "Medium"
        
        node = GraphNode(
            id=f"node_{idx}",
            title=e.source,
            subtitle="Anomaly Detected" if severity == "High" else "Telemetry",
            severity=severity,
            source=e.source,
            icon=icon
        )
        nodes.append(node)
        
    # Fully connect or linear sequence for simplicity
    if len(nodes) > 1:
        for i in range(len(nodes) - 1):
            edges.append(GraphEdge(
                id=f"edge_{i}_{i+1}",
                source=nodes[i].id,
                target=nodes[i+1].id,
                relationship="followed_by"
            ))
            
    return EvidenceGraph(nodes=nodes, edges=edges)
