"""
Manager for the deterministic Evidence Graph.
Provides safe mutators and graph traversal heuristics.
"""
from typing import List, Optional
from datetime import datetime
from backend.evidence.models import Evidence
from backend.correlation.models import InvestigationGraph, GraphNode, GraphEdge, ConfidenceScore

class EventGraphManager:
    """
    Wraps the raw InvestigationGraph Pydantic model.
    Provides deterministic algorithms to safely add edges and traverse relationships.
    Does NOT use external databases; entirely in-memory for Phase 2.
    """
    
    def __init__(self, graph: Optional[InvestigationGraph] = None):
        self.graph = graph or InvestigationGraph()
        
    def add_evidence(self, evidence: Evidence) -> GraphNode:
        """Adds a piece of evidence to the graph as a Node if it doesn't exist."""
        if evidence.id not in self.graph.nodes:
            node = GraphNode(id=evidence.id, evidence=evidence)
            self.graph.nodes[evidence.id] = node
        return self.graph.nodes[evidence.id]
        
    def add_relationship(
        self, 
        source_id: str, 
        target_id: str, 
        relationship_type: str, 
        confidence: ConfidenceScore,
        timestamp: Optional[datetime] = None
    ) -> GraphEdge:
        """
        Creates a directed edge between two existing nodes.
        relationship_type examples: 'Triggered', 'Depends On', 'Caused', 'Modified'
        """
        if source_id not in self.graph.nodes:
            raise ValueError(f"Source node {source_id} not in graph.")
        if target_id not in self.graph.nodes:
            raise ValueError(f"Target node {target_id} not in graph.")
            
        edge = GraphEdge(
            source_node_id=source_id,
            target_node_id=target_id,
            relationship_type=relationship_type,
            confidence=confidence,
            timestamp=timestamp or datetime.utcnow()
        )
        self.graph.edges.append(edge)
        return edge

    def get_related_edges(self, node_id: str) -> List[GraphEdge]:
        """Finds all edges (inbound or outbound) connected to a node."""
        return [
            e for e in self.graph.edges 
            if e.source_node_id == node_id or e.target_node_id == node_id
        ]
        
    def get_upstream_nodes(self, node_id: str, relationship_filter: Optional[str] = None) -> List[GraphNode]:
        """Finds nodes with edges pointing TO the target node."""
        edges = [
            e for e in self.graph.edges 
            if e.target_node_id == node_id
            and (not relationship_filter or e.relationship_type == relationship_filter)
        ]
        return [self.graph.nodes[e.source_node_id] for e in edges]

    def get_downstream_nodes(self, node_id: str, relationship_filter: Optional[str] = None) -> List[GraphNode]:
        """Finds nodes with edges pointing FROM the target node."""
        edges = [
            e for e in self.graph.edges 
            if e.source_node_id == node_id
            and (not relationship_filter or e.relationship_type == relationship_filter)
        ]
        return [self.graph.nodes[e.target_node_id] for e in edges]
