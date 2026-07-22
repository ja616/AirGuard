"""
Registry of supported incident definitions.
"""
from typing import Dict
from backend.taxonomy.models import IncidentDefinition, SeverityLevel
from backend.core.constants import IncidentCategory

def _create_incident(id, name, desc, severity, category, symptoms, req_ev, tools, signals, corr, conf, causes, rems, impact, fp, ext):
    return IncidentDefinition(
        id=id, name=name, description=desc, severity=severity, category=category,
        observable_symptoms=symptoms, required_evidence=req_ev, required_tools=tools,
        classification_signals=signals, correlation_strategy=corr, confidence_strategy=conf,
        possible_root_causes=causes, recommended_remediation=rems, business_impact=impact,
        false_positives=fp, future_extensions=ext
    )

INCIDENTS = [
    # Pillar 1 — Workflow Execution
    _create_incident(
        "INC-EXEC-001", "Task Retry Storm", "A task rapidly failing and retrying.",
        SeverityLevel.HIGH, IncidentCategory.WORKFLOW_EXECUTION, ["High Celery queue latency"],
        ["task_tries"], ["get_task_instance_history"], {"task_retry_count_high": 5.0, "retry_interval_short": 3.0},
        "Correlate task start times.", "High if >5 retries.", ["DB deadlock", "API 503"], ["Exp backoff"], "Worker starvation", ["Sensor tasks"], []
    ),
    _create_incident(
        "INC-DEP-001", "Dependency Failure", "Downstream fails due to upstream failure.",
        SeverityLevel.MEDIUM, IncidentCategory.WORKFLOW_EXECUTION, ["Dependent tasks not starting"],
        ["upstream_task_state"], ["get_task_instances"], {"upstream_task_failed": 5.0, "downstream_state_upstream_failed": 3.0},
        "Follow graph upstream.", "High if exact upstream failed.", ["Upstream code bug", "Bad data"], ["Fix upstream"], "Pipeline block", ["Skipped tasks"], []
    ),
    _create_incident(
        "INC-EXEC-002", "Task Failure", "Task fails with low/no retries.",
        SeverityLevel.MEDIUM, IncidentCategory.WORKFLOW_EXECUTION, ["Task state failed"],
        ["task_logs"], ["get_task_logs"], {"task_state_failed": 3.0, "task_retry_count_low": 2.0},
        "Extract exception.", "High if exception found.", ["Code bug"], ["Fix code"], "Task incomplete", ["Expected failure"], []
    ),
    _create_incident(
        "INC-EXEC-003", "Long Running Task", "Task runs beyond expected duration.",
        SeverityLevel.MEDIUM, IncidentCategory.WORKFLOW_EXECUTION, ["Task stuck running"],
        ["task_duration"], ["get_task_instances"], {"task_duration_high": 5.0, "task_state_running_timeout": 3.0},
        "Compare to baseline.", "High if >2x baseline.", ["Hanging query", "Deadlock"], ["Add timeout"], "Resource lock", ["Expected heavy processing"], []
    ),
    _create_incident(
        "INC-SCHED-001", "Scheduler Failure", "Airflow scheduler degraded or dead.",
        SeverityLevel.CRITICAL, IncidentCategory.WORKFLOW_EXECUTION, ["No tasks running", "Stale heartbeat"],
        ["scheduler_health"], ["get_scheduler_state"], {"scheduler_state_unhealthy": 6.0, "pending_tasks_age_high": 3.0},
        "Check health endpoint.", "High if health endpoint fails.", ["OOM", "DB disconnect"], ["Restart scheduler"], "System halted", ["Momentary blip"], []
    ),
    _create_incident(
        "INC-OPS-003", "DAG Pause / Resume", "DAG state toggled unexpectedly.",
        SeverityLevel.LOW, IncidentCategory.WORKFLOW_EXECUTION, ["Missed runs"],
        ["dag_graph"], ["get_dag_graph"], {"dag_paused_changed": 5.0, "missed_scheduled_runs": 3.0},
        "Check pause state.", "High if paused.", ["Accidental click"], ["Unpause"], "Missed SLAs", ["Intentional pause"], []
    ),
    
    # Pillar 2 — Data Readiness
    _create_incident(
        "INC-DATA-001", "Silent Data Failure", "Task succeeds but data is wrong.",
        SeverityLevel.HIGH, IncidentCategory.DATA_READINESS, ["Downstream alerts", "Empty tables"],
        ["xcoms"], ["get_task_instances"], {"task_state_success": 2.0, "xcom_quality_check_failed": 6.0, "xcom_row_count_zero": 3.0},
        "Check data quality XComs.", "High if XCom flags fail.", ["Empty source"], ["Fix source data"], "Bad analytics", ["Actually empty"], []
    ),
    _create_incident(
        "INC-DATA-002", "Missing Dataset", "Upstream data or object storage is empty.",
        SeverityLevel.HIGH, IncidentCategory.DATA_READINESS, ["Task fails immediately or sensor times out"],
        ["s3_metadata"], ["get_s3_prefix_metrics"], {"s3_prefix_empty": 5.0, "task_state_failed": 2.0},
        "Check prefix existence.", "High if S3 returns 0 bytes.", ["Upstream pipeline failure", "Late arrival"], ["Alert upstream owner"], "Stale data", ["New unpopulated dataset"], []
    ),

    # Pillar 3 — Compute & Infrastructure
    _create_incident(
        "INC-COMP-001", "Worker OOM (Exit Code 137)", "Task failed due to memory exhaustion.",
        SeverityLevel.HIGH, IncidentCategory.COMPUTE_INFRASTRUCTURE, ["Airflow worker crashes, exit code 137 in logs"],
        ["task_logs"], ["get_task_logs"], {"task_oom_killed": 6.0, "task_state_failed": 2.0},
        "Check for OOM signals.", "High if exit code 137 is explicitly logged.", ["Memory leak", "Large data payload"], ["Increase worker RAM"], "Task fails repeatedly", ["External kill"], []
    ),
    _create_incident(
        "INC-CLD-001", "Lambda Failure", "AWS Lambda invocation fails.",
        SeverityLevel.HIGH, IncidentCategory.COMPUTE_INFRASTRUCTURE, ["Airflow task fails, AWS alerts"],
        ["task_logs", "cloudwatch_metrics"], ["get_task_logs", "get_lambda_errors"], {"task_logs_contain_lambda": 3.0, "aws_lambda_error_count_high": 5.0},
        "Correlate task window with Lambda errors.", "High if AWS corroborates.", ["Bad payload", "Timeout"], ["Check Lambda logs"], "Integration broken", ["Throttling"], []
    ),
    _create_incident(
        "INC-EXEC-004", "Resource Contention", "Tasks queued but not running (Pools).",
        SeverityLevel.MEDIUM, IncidentCategory.COMPUTE_INFRASTRUCTURE, ["Tasks stuck queued"],
        ["pool_stats"], ["get_task_instances"], {"concurrent_tasks_high": 5.0, "pool_queued_slots_high": 3.0},
        "Check pool limits.", "High if queued slots > 0.", ["Pool too small"], ["Increase pool"], "Delays", ["Expected queueing"], []
    ),

    # Pillar 4 — ML Operations
    _create_incident(
        "INC-ML-001", "Training Failed", "Model training job failed.",
        SeverityLevel.HIGH, IncidentCategory.ML_OPERATIONS, ["Airflow task fails"],
        ["sagemaker_job_status"], ["get_sagemaker_job_status"], {"sagemaker_job_failed": 6.0, "task_state_failed": 2.0},
        "Check ML platform API.", "High if ML platform returns error.", ["OOM", "Bad hyperparameters"], ["Check ML logs"], "Model not deployed", ["Experimentation failure"], []
    ),

    # Pillar 5 — Cost & Operational Impact
    _create_incident(
        "INC-COST-001", "SageMaker Cost Spike", "ML job costs too much.",
        SeverityLevel.MEDIUM, IncidentCategory.COST_IMPACT, ["Billing alert"],
        ["task_duration", "aws_cost"], ["get_sagemaker_job_details"], {"sagemaker_duration_high": 4.0, "cost_delta_high": 4.0, "instance_type_changed": 2.0},
        "Correlate duration and type.", "High if instance changed.", ["Bad config"], ["Revert instance"], "Wasted money", ["Expected retraining"], []
    ),
    _create_incident(
        "INC-SCHED-003", "Backfill Storm", "Massive backfill blocks queue.",
        SeverityLevel.HIGH, IncidentCategory.COST_IMPACT, ["Queue full", "New tasks pending"],
        ["dag_runs"], ["get_dag_runs"], {"backfill_run_count_high": 5.0, "queued_tasks_high": 3.0},
        "Count backfill runs.", "High if >3 backfills.", ["Catchup enabled"], ["Pause backfill"], "Starvation", ["Intentional catchup"], []
    ),
    
    # Pillar 6 — Behavioural Anomalies
    _create_incident(
        "INC-BEHAV-001", "Runtime Anomaly", "A task or pipeline deviates significantly from historical runtime patterns.",
        SeverityLevel.LOW, IncidentCategory.BEHAVIOURAL_ANOMALY, ["SLA alerts", "Drift"],
        ["task_duration_history"], ["get_task_instances"], {"task_duration_anomaly": 6.0},
        "Compare to rolling average.", "Low (needs context).", ["Data skew", "System degradation"], ["Investigate downstream"], "Missed SLAs", ["Expected data volume increase"], []
    ),
    _create_incident(
        "INC-REC-001", "Partial Recovery", "Some tasks succeed after failure.",
        SeverityLevel.INFO, IncidentCategory.BEHAVIOURAL_ANOMALY, ["Mixed green/red"],
        ["task_states"], ["get_task_instances"], {"some_tasks_success": 3.0, "some_tasks_failed": 3.0, "previous_run_failed": 2.0},
        "Check states.", "High if mixed states.", ["Flaky API"], ["Clear failed"], "Incomplete data", ["Expected"], []
    )
]

INCIDENT_REGISTRY: Dict[str, IncidentDefinition] = {i.id: i for i in INCIDENTS}

def get_incident_definition(incident_id: str) -> IncidentDefinition:
    if incident_id not in INCIDENT_REGISTRY:
        raise ValueError(f"Incident ID {incident_id} not found in registry.")
    return INCIDENT_REGISTRY[incident_id]
