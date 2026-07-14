"""
Registry of supported incident definitions.
"""
from typing import Dict
from backend.taxonomy.models import IncidentDefinition, SeverityLevel
from backend.core.constants import IncidentCategory

# A sample of the core incidents defined as strongly typed models.
RETRY_STORM_INCIDENT = IncidentDefinition(
    id="INC-EXEC-001",
    name="Task Retry Storm",
    description="A single Airflow task or set of tasks rapidly failing and retrying, consuming worker slots.",
    severity=SeverityLevel.HIGH,
    category=IncidentCategory.EXECUTION,
    supported=True,
    observable_symptoms=[
        "High Celery queue latency",
        "Task try_number > 3 within 5 minutes",
        "Database connection pool exhaustion"
    ],
    required_evidence=[
        "Task instance history from Airflow DB",
        "Worker logs showing repeated exceptions",
        "CloudWatch metrics for RDS (CPU, connections)"
    ],
    required_tools=[
        "get_task_instance_history",
        "get_worker_logs",
        "get_cloudwatch_rds_metrics"
    ],
    correlation_strategy="Correlate task start times with spikes in RDS connections or CPU usage.",
    confidence_strategy="High if >5 retries in <10 mins AND corresponding metric spike exists.",
    possible_root_causes=[
        "Database deadlock",
        "API rate limiting from external service",
        "OOM kill on worker"
    ],
    recommended_remediation=[
        "Implement exponential backoff",
        "Increase pool size",
        "Clear task instance state"
    ],
    business_impact="Worker starvation leading to SLA breaches for other critical DAGs.",
    false_positives=[
        "Sensor tasks designed to poke continuously without rescheduling."
    ],
    future_extensions=[
        "Automated backoff injection"
    ]
)

COST_SPIKE_INCIDENT = IncidentDefinition(
    id="INC-COST-001",
    name="SageMaker Processing Cost Spike",
    description="A workflow utilizing AWS SageMaker incurred significantly higher costs than the baseline.",
    severity=SeverityLevel.MEDIUM,
    category=IncidentCategory.COST,
    supported=True,
    observable_symptoms=[
        "Billing alert triggered",
        "Task duration is unusually long"
    ],
    required_evidence=[
        "Airflow task execution duration",
        "AWS Cost Explorer data for specific tag/DAG",
        "SageMaker instance type and count used"
    ],
    required_tools=[
        "get_task_duration",
        "get_cost_explorer_metrics",
        "get_sagemaker_job_details"
    ],
    correlation_strategy="Match Airflow task execution window with AWS Cost Explorer hourly granularity.",
    confidence_strategy="Medium if cost > 2x baseline AND instance type changed.",
    possible_root_causes=[
        "Developer committed larger instance type",
        "Data volume increased 10x",
        "Job hung and ran to max timeout"
    ],
    recommended_remediation=[
        "Revert instance type change",
        "Set strict max_runtime on SageMaker job"
    ],
    business_impact="Unexpected cloud spend.",
    false_positives=[
        "Monthly aggregated billing updates appearing as sudden spikes."
    ],
    future_extensions=[
        "Proactive cost estimation before execution"
    ]
)

# Registry dictionary mapping ID to the definition
INCIDENT_REGISTRY: Dict[str, IncidentDefinition] = {
    RETRY_STORM_INCIDENT.id: RETRY_STORM_INCIDENT,
    COST_SPIKE_INCIDENT.id: COST_SPIKE_INCIDENT
}

def get_incident_definition(incident_id: str) -> IncidentDefinition:
    if incident_id not in INCIDENT_REGISTRY:
        raise ValueError(f"Incident ID {incident_id} not found in registry.")
    return INCIDENT_REGISTRY[incident_id]
