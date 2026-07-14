"""
Resource Correlation Strategy.
Maps Airflow concepts to underlying AWS Infrastructure ARNs.
"""
from typing import List
from backend.evidence.models import Evidence, TaskEvidence, MetricEvidence
from backend.correlation.interfaces import BaseCorrelator
from backend.correlation.models import InvestigationGraph, ConfidenceScore
from backend.correlation.event_graph import EventGraphManager

class ResourceCorrelator(BaseCorrelator):
    def correlate(self, evidence_pool: List[Evidence], graph: InvestigationGraph) -> None:
        manager = EventGraphManager(graph)
        
        for e in evidence_pool:
            manager.add_evidence(e)
            
        tasks = [e for e in evidence_pool if isinstance(e, TaskEvidence)]
        metrics = [e for e in evidence_pool if isinstance(e, MetricEvidence)]
        
        for task in tasks:
            for metric in metrics:
                # Rule: Exact tag match between Task ID and Metric dimension (e.g. SageMaker job name)
                task_arn = task.metadata.get("aws_resource_arn")
                metric_arn = metric.metadata.get("aws_resource_arn")
                
                if task_arn and metric_arn and task_arn == metric_arn:
                    manager.add_relationship(
                        source_id=task.id,
                        target_id=metric.id,
                        relationship_type="Executed On",
                        confidence=ConfidenceScore(
                            score=1.0,
                            reason="Exact ARN match between task execution and metric",
                            penalties=[]
                        )
                    )
