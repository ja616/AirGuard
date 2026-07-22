"""
AirGuard Failure Hook — Drop-in Airflow Callback
==================================================
A reusable callback factory that automatically triggers AirGuard investigations
when Airflow tasks or DAGs fail.

Usage:
    from dags.airguard_failure_hook import make_airguard_callback

    # Task-level failure (on_failure_callback)
    with DAG("my_dag", ...) as dag:
        task = PythonOperator(
            task_id="my_task",
            on_failure_callback=make_airguard_callback(),
            ...
        )

    # DAG-level failure (catches any task failure in the DAG)
    with DAG(
        "my_dag",
        on_failure_callback=make_airguard_callback("dag_failure", severity="high"),
        ...
    ) as dag:
        ...

    # SLA miss
    with DAG(
        "my_dag",
        sla_miss_callback=make_airguard_callback("sla_miss"),
        ...
    ) as dag:
        ...

    # Retry callback — investigate after every retry
    task = PythonOperator(
        task_id="my_task",
        on_retry_callback=make_airguard_callback("task_retry", severity="low"),
        ...
    )
"""
import os
import logging
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

logger = logging.getLogger("airguard_failure_hook")

# ─────────────────────────────────────────────────────────────────────────────
# Configuration (read from environment at import time)
# ─────────────────────────────────────────────────────────────────────────────

AIRGUARD_URL = os.getenv("AIRGUARD_URL", "http://localhost:8000")
AIRGUARD_WEBHOOK_TOKEN = os.getenv("AIRGUARD_WEBHOOK_TOKEN", "")
AIRGUARD_DEFAULT_ENVIRONMENT = os.getenv("AIRGUARD_ENVIRONMENT", "prod")


# ─────────────────────────────────────────────────────────────────────────────
# Callback factory
# ─────────────────────────────────────────────────────────────────────────────

def make_airguard_callback(
    callback_type: str = "task_failure",
    severity: Optional[str] = None,
    investigation_goal: str = "root_cause",
    environment: Optional[str] = None,
    timeout_seconds: int = 5,
):
    """
    Returns a callable suitable for use as an Airflow on_failure_callback,
    on_retry_callback, sla_miss_callback, or DAG-level on_failure_callback.

    Args:
        callback_type: One of: task_failure, task_retry, sla_miss, dag_failure.
        severity: Override inferred severity. One of: critical, high, medium, low.
        investigation_goal: One of: root_cause, impact_analysis, cost_analysis, performance.
        environment: Override deployment environment. One of: dev, staging, prod.
        timeout_seconds: HTTP request timeout in seconds (non-blocking if exceeded).
    """
    _env = environment or AIRGUARD_DEFAULT_ENVIRONMENT

    def _callback(context: dict):
        """The actual Airflow callback function. context = Airflow's context dict."""
        if requests is None:
            logger.error("[AirGuard] 'requests' library not available. Cannot send webhook.")
            return

        # Extract fields from Airflow's context dict
        dag = context.get("dag")
        dag_run = context.get("dag_run")
        task_instance = context.get("task_instance")

        dag_id = (
            getattr(dag, "dag_id", None) or
            getattr(dag_run, "dag_id", None) or
            context.get("dag_id", "unknown")
        )
        run_id = getattr(dag_run, "run_id", None) or context.get("run_id")
        task_id = getattr(task_instance, "task_id", None) or context.get("task_id")
        execution_date = (
            str(getattr(dag_run, "execution_date", None) or
                getattr(task_instance, "execution_date", None) or
                context.get("execution_date", ""))
        )
        try_number = getattr(task_instance, "try_number", None)
        state = getattr(task_instance, "state", None)

        # Capture exception info if available
        exception = context.get("exception")
        exception_str = str(exception) if exception else None

        # Log URL for direct task log access
        try:
            log_url = task_instance.log_url if task_instance else None
        except Exception:
            log_url = None

        payload = {
            "callback_type": callback_type,
            "dag_id": dag_id,
            "run_id": run_id,
            "task_id": task_id if callback_type != "dag_failure" else None,
            "execution_date": execution_date,
            "try_number": try_number,
            "state": state,
            "exception": exception_str,
            "log_url": log_url,
            "severity": severity,
            "environment": _env,
            "investigation_goal": investigation_goal,
        }

        webhook_url = f"{AIRGUARD_URL}/api/v1/airflow/webhook"
        headers = {
            "Content-Type": "application/json",
            "X-AirGuard-Token": AIRGUARD_WEBHOOK_TOKEN,
        }

        try:
            resp = requests.post(webhook_url, json=payload, headers=headers, timeout=timeout_seconds)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(
                    f"[AirGuard] Investigation started: {data.get('investigation_id')} | "
                    f"dag={dag_id} | severity={data.get('severity')} | "
                    f"callback_type={callback_type}"
                )
            else:
                logger.error(
                    f"[AirGuard] Webhook rejected: HTTP {resp.status_code} — {resp.text[:200]}"
                )
        except requests.exceptions.Timeout:
            logger.warning(
                f"[AirGuard] Webhook timed out after {timeout_seconds}s for dag={dag_id}. "
                "Investigation NOT triggered. Check AirGuard connectivity."
            )
        except Exception as e:
            logger.error(f"[AirGuard] Failed to send webhook: {e}")

    return _callback
