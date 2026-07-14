import uuid
from typing import Dict, Any
from backend.domain.evidence import AirflowTaskEvidence

def map_task_instance_to_evidence(raw_ti: Dict[str, Any], logs: str = "") -> AirflowTaskEvidence:
    """Strict mapping from raw Airflow REST JSON to Evidence model."""
    return AirflowTaskEvidence(
        id=str(uuid.uuid4()),
        dag_id=raw_ti.get("dag_id", "unknown_dag"),
        run_id=raw_ti.get("dag_run_id", "unknown_run"),
        task_id=raw_ti.get("task_id", "unknown_task"),
        state=raw_ti.get("state", "unknown"),
        log_preview=logs[:500] if logs else "",
        payload=raw_ti
    )
