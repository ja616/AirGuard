"""
Temporal Correlation Strategy.
Matches events based on strict chronological windows.
"""
from typing import List
from datetime import timedelta
from backend.evidence.models import Evidence, TaskEvidence, CloudTrailEvidence
from backend.correlation.interfaces import BaseCorrelator
from backend.correlation.models import InvestigationGraph, ConfidenceScore
from backend.correlation.event_graph import EventGraphManager

class TemporalCorrelator(BaseCorrelator):
    def __init__(self, window_minutes: int = 15):
        self.window = timedelta(minutes=window_minutes)

    def correlate(self, evidence_pool: List[Evidence], graph: InvestigationGraph) -> None:
        manager = EventGraphManager(graph)
        
        # Ensure all evidence is present as nodes
        for e in evidence_pool:
            manager.add_evidence(e)
            
        tasks = [e for e in evidence_pool if isinstance(e, TaskEvidence) and e.state == "failed"]
        trails = [e for e in evidence_pool if isinstance(e, CloudTrailEvidence)]
        
        for task in tasks:
            for trail in trails:
                # Rule: CloudTrail event happened BEFORE task failure, within the window
                time_diff = task.timestamp - trail.timestamp
                if timedelta(minutes=0) <= time_diff <= self.window:
                    # Confidence heuristic: closer in time = higher score
                    score = max(0.1, 1.0 - (time_diff.total_seconds() / self.window.total_seconds()))
                    manager.add_relationship(
                        source_id=trail.id,
                        target_id=task.id,
                        relationship_type="Potentially Caused",
                        confidence=ConfidenceScore(
                            score=round(score, 2),
                            reason=f"Temporal correlation within {self.window.total_seconds() / 60}m window",
                            penalties=[]
                        )
                    )
