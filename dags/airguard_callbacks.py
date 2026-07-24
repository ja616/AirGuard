"""
Webhook callback utility for AirGuard auto-investigation.

Placed here so any DAG can import it with:
    from airguard_callbacks import notify_airguard_failure, notify_airguard_retry
"""
import logging

log = logging.getLogger(__name__)

AIRGUARD_URL = "http://airguard-backend:8000/api/v1/airflow/webhook"
# Token must match AIRGUARD_WEBHOOK_TOKEN in .env.local / environment
AIRGUARD_TOKEN = "airguard-local-dev-secret-2026"


def _post(payload: dict) -> None:
    """Fire-and-forget POST to AirGuard webhook. Never raises — failures are logged."""
    try:
        import requests
        resp = requests.post(
            AIRGUARD_URL,
            json=payload,
            headers={"X-AirGuard-Token": AIRGUARD_TOKEN},
            timeout=5,
        )
        if resp.ok:
            log.info(f"[AirGuard] Investigation queued: {resp.json().get('investigation_id')}")
        else:
            log.warning(f"[AirGuard] Webhook rejected ({resp.status_code}): {resp.text[:200]}")
    except Exception as exc:
        # Never let the callback kill the Airflow task tracking
        log.warning(f"[AirGuard] Webhook failed (non-fatal): {exc}")


def notify_airguard_failure(context: dict) -> None:
    """on_failure_callback — fires when a task exhausts all retries and is permanently FAILED."""
    ti = context.get("task_instance")
    _post({
        "callback_type": "task_failure",
        "dag_id": context["dag"].dag_id,
        "run_id": context.get("run_id") or (ti.run_id if ti else None),
        "task_id": ti.task_id if ti else None,
        "try_number": ti.try_number if ti else None,
        "state": "failed",
        "exception": str(context.get("exception", "")),
        "environment": "prod",
        "investigation_goal": "root_cause",
    })


def notify_airguard_retry(context: dict) -> None:
    """on_retry_callback — fires on every retry attempt."""
    ti = context.get("task_instance")
    _post({
        "callback_type": "task_retry",
        "dag_id": context["dag"].dag_id,
        "run_id": context.get("run_id") or (ti.run_id if ti else None),
        "task_id": ti.task_id if ti else None,
        "try_number": ti.try_number if ti else None,
        "state": "up_for_retry",
        "exception": str(context.get("exception", "")),
        "environment": "prod",
        "investigation_goal": "root_cause",
    })


def notify_airguard_dag_failure(context: dict) -> None:
    """DAG-level on_failure_callback."""
    _post({
        "callback_type": "dag_failure",
        "dag_id": context["dag"].dag_id,
        "run_id": context.get("run_id"),
        "task_id": None,
        "state": "failed",
        "environment": "prod",
        "investigation_goal": "root_cause",
    })
