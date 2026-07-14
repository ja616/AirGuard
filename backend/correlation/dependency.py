"""
Dependency Correlation Strategy.
Maps upstream blockages via deterministic DAG paths.
"""
from typing import List
from backend.evidence.models import Evidence, TaskEvidence, DependencyEvidence
from backend.correlation.interfaces import BaseCorrelator
from backend.correlation.models import InvestigationGraph, ConfidenceScore
from backend.correlation.event_graph import EventGraphManager

class DependencyCorrelator(BaseCorrelator):
    def correlate(self, evidence_pool: List[Evidence], graph: InvestigationGraph) -> None:
        manager = EventGraphManager(graph)
        
        for e in evidence_pool:
            manager.add_evidence(e)
            
        tasks = {e.task_id: e for e in evidence_pool if isinstance(e, TaskEvidence)}
        deps = [e for e in evidence_pool if isinstance(e, DependencyEvidence)]
        
        for dep in deps:
            if dep.upstream_task_id in tasks and dep.downstream_task_id in tasks:
                up_id = tasks[dep.upstream_task_id].id
                down_id = tasks[dep.downstream_task_id].id
                manager.add_relationship(
                    source_id=up_id,
                    target_id=down_id,
                    relationship_type="Blocks",
                    confidence=ConfidenceScore(
                        score=1.0,
                        reason="Deterministic Airflow DAG definition",
                        penalties=[]
                    )
                )
