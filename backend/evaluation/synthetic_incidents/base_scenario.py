"""
Abstract interface for all Synthetic Scenarios.
"""
from abc import ABC, abstractmethod
from typing import List
from backend.evidence.models import Evidence
from backend.evaluation.models import GroundTruth

class BaseSyntheticScenario(ABC):
    """
    A strictly defined, reproducible operational incident.
    Must generate its own deterministic evidence and define its ground truth.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def difficulty(self) -> str:
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        pass

    @property
    @abstractmethod
    def context(self) -> str:
        pass

    @abstractmethod
    def generate_evidence(self) -> List[Evidence]:
        """Returns the unordered pool of synthetic evidence representing the incident state."""
        pass

    @abstractmethod
    def get_ground_truth(self) -> GroundTruth:
        """Returns the deterministic answers the pipeline must reach."""
        pass
