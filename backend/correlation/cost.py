"""
Cost Attribution Strategy.
Maps AWS Cost Explorer data deterministically to Workflow Tasks.
Implements a Weighted Evidence Aggregation hierarchy.
"""
from typing import List
from datetime import timedelta
from backend.evidence.models import Evidence, TaskEvidence, CostEvidence, ScheduleEvidence, CloudTrailEvidence
from backend.correlation.interfaces import BaseCorrelator
from backend.correlation.models import InvestigationGraph, ConfidenceScore
from backend.correlation.event_graph import EventGraphManager

class CostCorrelator(BaseCorrelator):
    def correlate(self, evidence_pool: List[Evidence], graph: InvestigationGraph) -> None:
        manager = EventGraphManager(graph)
        
        for e in evidence_pool:
            manager.add_evidence(e)
            
        tasks = [e for e in evidence_pool if isinstance(e, TaskEvidence)]
        costs = [e for e in evidence_pool if isinstance(e, CostEvidence)]
        
        # Pre-filter Tier 3 Evidence for performance
        ecosystem_events = [e for e in evidence_pool if isinstance(e, (ScheduleEvidence, CloudTrailEvidence))]
        
        for cost in costs:
            for task in tasks:
                score = 0.0
                reason_parts = []
                penalties = []
                
                # --- Tier 1: Deterministic Identity ---
                cost_task_tag = cost.metadata.get("tag:airflow_task_id")
                task_arn = task.metadata.get("aws_resource_arn")
                cost_arn = cost.metadata.get("aws_resource_arn")
                
                if cost_task_tag and cost_task_tag == task.task_id:
                    score += 1.0
                    reason_parts.append("Exact AWS billing tag match")
                elif task_arn and cost_arn and task_arn == cost_arn:
                    score += 0.70
                    reason_parts.append("ARN mapped to billing dimension")
                    penalties.append("Missing exact cost allocation tag")
                else:
                    continue # No base linkage found, skip
                    
                # --- Tier 2: Temporal Overlap ---
                if score < 1.0:
                    time_diff = abs((cost.timestamp - task.timestamp).total_seconds())
                    if time_diff <= 7200: # Cost incurred within 2 hours of task
                        score += 0.20
                        reason_parts.append("Execution time overlaps with cost window")
                        
                # --- Tier 3: Ecosystem Anomalies ---
                if score < 1.0:
                    for anomaly in ecosystem_events:
                        time_diff = abs((anomaly.timestamp - task.timestamp).total_seconds())
                        if time_diff <= 86400: # Within 24 hours of anomalous schedule change
                            score += 0.10
                            reason_parts.append("Correlated with parallel schedule anomaly")
                            break
                            
                final_score = min(1.0, score)
                
                # If we achieved full confidence via weighted context, forgive the tag penalty
                if final_score >= 1.0:
                    penalties = []
                    
                manager.add_relationship(
                    source_id=task.id,
                    target_id=cost.id,
                    relationship_type="Incurred",
                    confidence=ConfidenceScore(
                        score=round(final_score, 2),
                        reason=" | ".join(reason_parts),
                        penalties=penalties
                    )
                )
