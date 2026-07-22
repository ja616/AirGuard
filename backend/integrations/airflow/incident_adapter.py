"""
Airflow → IncidentContext Adapter
===================================
This is the ONLY place in the backend where Airflow-specific field names appear.

All orchestrator-specific concepts are mapped to generic domain terms here
before entering the rest of the system.

Mapping:
    Airflow             → Generic domain (IncidentContext)
    ─────────────────────────────────────────────────────
    dag_id              → workflow_id
    dag_run_id / run_id → workflow_execution_id
    task_id             → failed_node_id
    state               → execution_state
    try_number          → retry_number
    exception string    → orchestrator_error_type
    execution_date      → execution_timestamp
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

from backend.investigation.models import IncidentContext, TriggerSource, IncidentSeverity


class AirflowCallbackType(str, Enum):
    TASK_FAILURE = "task_failure"   # on_failure_callback
    TASK_RETRY = "task_retry"       # on_retry_callback
    SLA_MISS = "sla_miss"           # sla_miss_callback
    DAG_FAILURE = "dag_failure"     # DAG-level on_failure_callback


def _parse_dt(dt_str: Optional[str]) -> datetime:
    """Safely parse an ISO datetime string, falling back to now."""
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)


def _infer_severity(
    payload: dict,
    callback_type: AirflowCallbackType,
) -> IncidentSeverity:
    """
    Infer incident severity from Airflow callback context.
    The caller can override this by passing severity explicitly.
    """
    try_number = payload.get("try_number") or 0
    dag_id = (payload.get("dag_id") or "").lower()

    # SLA misses in production are always HIGH
    if callback_type == AirflowCallbackType.SLA_MISS:
        return IncidentSeverity.HIGH

    # DAG-level failures are more severe than task-level
    if callback_type == AirflowCallbackType.DAG_FAILURE:
        return IncidentSeverity.HIGH

    # Many retries escalate severity
    if try_number >= 5:
        return IncidentSeverity.CRITICAL
    if try_number >= 3:
        return IncidentSeverity.HIGH

    # Critical DAG IDs (convention-based)
    critical_patterns = ("critical", "prod", "payment", "revenue", "alert")
    if any(p in dag_id for p in critical_patterns):
        return IncidentSeverity.HIGH

    return IncidentSeverity.MEDIUM


def from_airflow_callback(
    payload: dict,
    callback_type: AirflowCallbackType = AirflowCallbackType.TASK_FAILURE,
    severity_override: Optional[IncidentSeverity] = None,
    environment: str = "prod",
    investigation_goal_str: str = "root_cause",
) -> IncidentContext:
    """
    Convert an Airflow on_failure_callback / on_retry_callback / sla_miss_callback
    context dict into a generic IncidentContext.

    Args:
        payload: The raw Airflow callback context dict.
        callback_type: Which Airflow callback fired.
        severity_override: If provided, overrides the inferred severity.
        environment: Deployment environment (dev/staging/prod).
        investigation_goal_str: String form of InvestigationGoal enum value.
    """
    from backend.investigation.models import InvestigationGoal

    # Map Airflow-specific fields → generic domain fields
    workflow_id = payload.get("dag_id") or payload.get("dag", {}).get("dag_id", "unknown")
    workflow_execution_id = payload.get("run_id") or payload.get("dag_run_id")
    failed_node_id = payload.get("task_id") or payload.get("task_instance_key", {}).get("task_id")
    execution_timestamp = _parse_dt(payload.get("execution_date") or payload.get("data_interval_start"))
    execution_state = payload.get("state", "failed")
    retry_number = payload.get("try_number")

    # Extract error info
    exception = payload.get("exception")
    orchestrator_error_type = str(type(exception).__name__) if exception and not isinstance(exception, str) else str(exception or "")

    # Build additional_context for audit trail
    additional_context: dict[str, str] = {}
    if payload.get("log_url"):
        additional_context["log_url"] = payload["log_url"]
    if orchestrator_error_type:
        additional_context["exception"] = orchestrator_error_type[:500]  # cap length
    additional_context["callback_type"] = callback_type.value
    if callback_type == AirflowCallbackType.SLA_MISS and payload.get("sla_miss_info"):
        additional_context["sla_miss_info"] = str(payload["sla_miss_info"])[:500]

    severity = severity_override or _infer_severity(payload, callback_type)

    # Parse investigation goal
    try:
        goal = InvestigationGoal(investigation_goal_str)
    except ValueError:
        goal = InvestigationGoal.ROOT_CAUSE

    return IncidentContext(
        workflow_id=workflow_id,
        workflow_execution_id=workflow_execution_id,
        failed_node_id=failed_node_id,
        execution_timestamp=execution_timestamp,
        severity=severity,
        trigger_source=TriggerSource.ORCHESTRATOR_CALLBACK,
        environment=environment,  # type: ignore[arg-type]
        investigation_goal=goal,
        execution_state=execution_state,
        retry_number=retry_number,
        orchestrator_error_type=orchestrator_error_type or None,
        additional_context=additional_context,
    )
