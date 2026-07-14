"""
Abstract interfaces for the deterministic correlators.
"""
from abc import ABC, abstractmethod
from typing import List
from backend.evidence.models import Evidence
from backend.correlation.models import InvestigationGraph

class BaseCorrelator(ABC):
    """
    Every correlation strategy (Temporal, Dependency, Resource, Cost) 
    must implement this interface. 
    It is strictly a deterministic mutator of the InvestigationGraph.
    """
    
    @abstractmethod
    def correlate(self, evidence_pool: List[Evidence], graph: InvestigationGraph) -> None:
        """
        Analyzes the evidence pool, identifies relationships based on hardcoded rules,
        and deterministically adds GraphEdges to the provided graph in-place.
        """
        pass
