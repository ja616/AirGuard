"""
Evidence Collection Capability Tools.
Purpose: Collect deterministic evidence from underlying systems.
"""
from backend.evidence.models import TaskEvidence
from backend.evidence.builder import EvidenceBuilder
from backend.tools.decorators import deterministic_tool
from datetime import datetime

@deterministic_tool(timeout=15, retries=3, required_permissions=["airflow.task_logs.read"])
def collect_task_logs(dag_id: str, task_id: str, execution_date: str) -> TaskEvidence:
    """
    Purpose: Collect task logs to extract deterministic error signatures.
    Inputs: dag_id, task_id, execution_date
    Outputs: TaskEvidence
    Permissions: airflow.task_logs.read
    Underlying SDK: apache-airflow-client (mocked)
    Retries: 3
    Timeout: 15s
    Rate Limits: 50/min
    Caching: None
    Logging: Enforced via decorator
    Metrics: tool.collection.success, tool.collection.bytes_read
    Observability: Datadog tracing enabled
    Failure Modes: Log file missing, S3 timeout
    Exceptions: LogNotFoundException
    """
    raw_data = {
        "log_content": "ERROR - Database connection pool exhausted",
        "execution_date": execution_date
    }
    
    return EvidenceBuilder.build_task_evidence(
        source="airflow_task_logs",
        raw_data=raw_data,
        dag_id=dag_id,
        task_id=task_id,
        state="failed",
        timestamp=datetime.utcnow()
    )
