"""
Airflow Webhook Endpoint
========================
Authenticated endpoint for Airflow (and other orchestrators) to push failure
events directly to AirGuard.

Supports all four Airflow callback types:
    POST /api/v1/airflow/webhook  → task_failure, task_retry, sla_miss, dag_failure

Authentication:
    X-AirGuard-Token header (constant-time comparison against AIRGUARD_WEBHOOK_TOKEN env var).

The raw payload is normalized into a generic IncidentContext by the Airflow adapter,
which is the only place Airflow-specific field names appear in the backend.
"""
from __future__ import annotations
import hmac
import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel

from backend.integrations.core.config import config
from backend.integrations.airflow.incident_adapter import (
    from_airflow_callback,
    AirflowCallbackType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/airflow", tags=["Airflow Integration"])


# ─────────────────────────────────────────────────────────────────────────────
# Auth helper
# ─────────────────────────────────────────────────────────────────────────────

def _verify_token(provided: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    expected = config.airguard_webhook_token
    if not expected:
        logger.warning("AIRGUARD_WEBHOOK_TOKEN is not set. Webhook is unauthenticated.")
        return True  # Permissive when token not configured (local dev)
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


# ─────────────────────────────────────────────────────────────────────────────
# Request model — mirrors Airflow's callback context dict
# ─────────────────────────────────────────────────────────────────────────────

class AirflowWebhookPayload(BaseModel):
    """
    Structured representation of an Airflow callback payload.
    Maps directly to what Airflow passes in on_failure_callback context.
    """
    callback_type: str = "task_failure"  # task_failure|task_retry|sla_miss|dag_failure
    dag_id: str
    run_id: Optional[str] = None
    task_id: Optional[str] = None          # null for DAG-level and SLA callbacks
    execution_date: Optional[str] = None
    try_number: Optional[int] = None
    state: Optional[str] = None
    exception: Optional[str] = None
    log_url: Optional[str] = None
    sla_miss_info: Optional[dict] = None   # for SLA callbacks
    # Optional caller overrides
    severity: Optional[str] = None         # override auto-inferred severity
    environment: str = "prod"
    investigation_goal: str = "root_cause"


# ─────────────────────────────────────────────────────────────────────────────
# Webhook endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/webhook")
async def airflow_webhook(
    payload: AirflowWebhookPayload,
    background_tasks: BackgroundTasks,
    x_airguard_token: Optional[str] = Header(default=None, alias="X-AirGuard-Token"),
):
    """
    Receive an Airflow failure/retry/SLA/DAG-level event and start an investigation.

    Supported callback_type values:
      - task_failure   → on_failure_callback (default)
      - task_retry     → on_retry_callback
      - sla_miss       → sla_miss_callback
      - dag_failure    → DAG-level on_failure_callback
    """
    # ── Authentication ───────────────────────────────────────────────────────
    token = x_airguard_token or ""
    if not _verify_token(token):
        logger.warning(
            f"Rejected webhook for dag_id='{payload.dag_id}' — invalid token."
        )
        raise HTTPException(status_code=401, detail="Invalid or missing X-AirGuard-Token")

    # ── Parse callback type ───────────────────────────────────────────────────
    try:
        cb_type = AirflowCallbackType(payload.callback_type)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown callback_type '{payload.callback_type}'. "
                   f"Valid values: {[e.value for e in AirflowCallbackType]}"
        )

    # ── Normalize to IncidentContext ──────────────────────────────────────────
    from backend.investigation.models import IncidentSeverity
    severity_override = None
    if payload.severity:
        try:
            severity_override = IncidentSeverity(payload.severity)
        except ValueError:
            pass  # Ignore invalid severity — adapter will infer it

    raw_payload = {
        "dag_id": payload.dag_id,
        "run_id": payload.run_id,
        "task_id": payload.task_id,
        "execution_date": payload.execution_date,
        "try_number": payload.try_number,
        "state": payload.state,
        "exception": payload.exception,
        "log_url": payload.log_url,
        "sla_miss_info": payload.sla_miss_info,
    }

    incident_context = from_airflow_callback(
        payload=raw_payload,
        callback_type=cb_type,
        severity_override=severity_override,
        environment=payload.environment,
        investigation_goal_str=payload.investigation_goal,
    )

    # ── Create investigation via shared DI service ─────────────────────────────
    from backend.api.dependencies import get_investigation_service

    service = get_investigation_service()
    inv = service.create_investigation(
        started_by="airflow_webhook",
        airflow_environment=payload.environment,
    )
    background_tasks.add_task(
        service.execute_investigation_pipeline_async_context,
        inv.id,
        incident_context,
    )
    logger.info(
        f"Investigation {inv.id} started for dag='{payload.dag_id}' "
        f"callback_type={cb_type.value} severity={incident_context.severity.value}"
    )
    return {
        "investigation_id": inv.id,
        "state": inv.state,
        "dag_id": payload.dag_id,
        "callback_type": cb_type.value,
        "severity": incident_context.severity.value,
        "environment": incident_context.environment,
    }
