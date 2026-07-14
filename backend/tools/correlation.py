"""
Correlation Capability Tools.
Purpose: Transform evidence into relationships (stubbed for Phase 2).
"""
from backend.tools.decorators import deterministic_tool

@deterministic_tool(timeout=30, retries=1, required_permissions=["internal.graph.write"])
def build_evidence_graph(evidence_list: list) -> dict:
    """
    Purpose: Build graph connecting collected evidence.
    Outputs: Graph structure (Implementation deferred to Phase 2)
    """
    return {"nodes": len(evidence_list), "edges": 0}
