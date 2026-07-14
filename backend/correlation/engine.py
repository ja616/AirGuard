"""
The master orchestrator for the Phase 2 Correlation Engine.
"""
from typing import List
from backend.evidence.models import Evidence
from backend.correlation.models import InvestigationGraph, CorrelationResult
from backend.correlation.temporal import TemporalCorrelator
from backend.correlation.dependency import DependencyCorrelator
from backend.correlation.resource import ResourceCorrelator
from backend.correlation.cost import CostCorrelator
from backend.correlation.timeline import TimelineBuilder

class CorrelationEngine:
    """
    Transforms disconnected evidence into an Investigation Graph.
    Executes all deterministic correlators sequentially.
    """
    def __init__(self):
        # Initialize all strategies in execution order
        self.correlators = [
            TemporalCorrelator(),
            DependencyCorrelator(),
            ResourceCorrelator(),
            CostCorrelator()
        ]

    def process(self, evidence_pool: List[Evidence]) -> CorrelationResult:
        """
        The main entrypoint for Phase 2.
        Takes evidence, runs all heuristics, and returns the strictly typed CorrelationResult.
        """
        graph = InvestigationGraph()
        
        # 1. Mutate the graph with all correlation strategies
        for correlator in self.correlators:
            correlator.correlate(evidence_pool, graph)
            
        # 2. Extract chronological timeline
        timeline = TimelineBuilder.build_timeline(graph)
        
        # 3. Extract specialized views from the graph (Stubbed for now, full extraction is trivial graph traversal)
        resource_links = []
        cost_attribution = None
        dependency_chains = []
        
        return CorrelationResult(
            graph=graph,
            timeline=timeline,
            resource_links=resource_links,
            cost_attribution=cost_attribution,
            dependency_chains=dependency_chains
        )
