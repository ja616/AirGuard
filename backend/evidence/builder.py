"""
Builders to construct strict Evidence objects from raw tool payloads.
"""
from datetime import datetime
from typing import Any, Dict
from backend.evidence.models import TaskEvidence, MetricEvidence

class EvidenceBuilder:
    """
    Centralizes the mapping from messy API responses to clean, 
    Correlation-Engine-ready Evidence objects.
    """
    
    @staticmethod
    def build_task_evidence(
        source: str, 
        raw_data: Dict[str, Any], 
        dag_id: str, 
        task_id: str, 
        state: str, 
        timestamp: datetime
    ) -> TaskEvidence:
        return TaskEvidence(
            source=source,
            timestamp=timestamp,
            reliability=1.0, # Airflow Metadata DB is highly reliable
            confidence=1.0,
            raw_payload=raw_data,
            normalized_payload={"state": state, "dag_id": dag_id, "task_id": task_id},
            dag_id=dag_id,
            task_id=task_id,
            execution_date=raw_data.get("execution_date", ""),
            state=state
        )

    @staticmethod
    def build_metric_evidence(
        source: str,
        raw_data: Dict[str, Any],
        metric_name: str,
        value: float,
        unit: str,
        timestamp: datetime
    ) -> MetricEvidence:
        return MetricEvidence(
            source=source,
            timestamp=timestamp,
            reliability=0.9, # CloudWatch is reliable but aggregated
            confidence=1.0,
            raw_payload=raw_data,
            normalized_payload={"metric": metric_name, "value": value},
            metric_name=metric_name,
            value=value,
            unit=unit
        )
