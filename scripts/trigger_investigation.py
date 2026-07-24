"""
AirGuard Investigation Trigger Script
======================================
Demonstrates both the new structured IncidentContext payload and the legacy user_query path.
"""
import requests
import json

BASE_URL = "http://localhost:8000"
WEBHOOK_TOKEN = "airguard-local-dev-secret-2026"


def trigger_structured(dag_id: str, failed_node_id: str = None, severity: str = "high",
                        run_id: str = None, execution_state: str = "failed",
                        goal: str = "root_cause", retry_number: int = None):
    """Trigger via new structured IncidentContext path."""
    payload = {
        "dag_id": dag_id,
        "severity": severity,
        "investigation_goal": goal,
        "environment": "prod",
        "execution_state": execution_state,
    }
    if failed_node_id:
        payload["failed_node_id"] = failed_node_id
    if run_id:
        payload["workflow_execution_id"] = run_id
    if retry_number is not None:
        payload["retry_number"] = retry_number

    print(f"\n[Structured] Triggering investigation for dag='{dag_id}'")
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    resp = requests.post(f"{BASE_URL}/api/v1/investigations/", json=payload)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {resp.json()}")
    return resp.json()


def trigger_legacy(dag_id: str, user_query: str):
    """Trigger via legacy user_query path (backward compat)."""
    payload = {"dag_id": dag_id, "user_query": user_query}
    print(f"\n[Legacy] Triggering investigation for dag='{dag_id}'")
    print(f"  user_query: {user_query}")
    resp = requests.post(f"{BASE_URL}/api/v1/investigations/", json=payload)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {resp.json()}")
    return resp.json()


def trigger_via_webhook(dag_id: str, task_id: str, callback_type: str = "task_failure",
                        run_id: str = None, try_number: int = 3):
    """Trigger via the Airflow webhook endpoint (requires auth token)."""
    payload = {
        "callback_type": callback_type,
        "dag_id": dag_id,
        "run_id": run_id,
        "task_id": task_id,
        "try_number": try_number,
        "state": "failed",
        "exception": "AirflowException: Task failed after exhausting retries",
        "environment": "prod",
        "severity": "high",
        "investigation_goal": "root_cause",
    }
    headers = {"X-AirGuard-Token": WEBHOOK_TOKEN}
    print(f"\n[Webhook] Triggering {callback_type} for dag='{dag_id}' task='{task_id}'")
    resp = requests.post(f"{BASE_URL}/api/v1/airflow/webhook", json=payload, headers=headers)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {resp.json()}")
    return resp.json()


def test_webhook_auth_rejection():
    """Verify that the webhook rejects requests with wrong token."""
    payload = {"callback_type": "task_failure", "dag_id": "test_dag"}
    headers = {"X-AirGuard-Token": "wrong-token"}
    resp = requests.post(f"{BASE_URL}/api/v1/airflow/webhook", json=payload, headers=headers)
    print(f"\n[Auth Test] Status (expected 401): {resp.status_code}")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
    print("  ✓ Auth rejection working correctly")


if __name__ == "__main__":
    print("=" * 60)
    print("AirGuard Investigation Trigger Demo")
    print("=" * 60)

    # 1. New structured path
    trigger_structured(
        dag_id="data_pipeline_etl",
        failed_node_id="extract_raw_data",
        severity="high",
        execution_state="failed",
        retry_number=3,
        goal="root_cause",
    )

    # 2. Legacy path (still works)
    # trigger_legacy(
    #     dag_id="data_pipeline_etl",
    #     user_query="ETL pipeline failing with Lambda throttles and S3 latency",
    # )

    # 3. Airflow webhook path
    # trigger_via_webhook(
    #     dag_id="data_pipeline_etl",
    #     task_id="extract_raw_data",
    #     callback_type="task_failure",
    #     run_id="scheduled__2026-07-21T00:00:00+00:00",
    #     try_number=3,
    # )

    # 4. Auth rejection test
    # test_webhook_auth_rejection()

    # 5. DEMO: The Phantom Retraining Storm (Cost Spike)
    # trigger_structured(
    #     dag_id="ml_training_pipeline",
    #     severity="critical",
    #     execution_state="success",
    #     goal="cost_analysis",
    # )

    # 6. DEMO: SageMaker Timeout Loop
    trigger_structured(
        dag_id="daily_ml_pipeline",
        failed_node_id="train_sagemaker_model",
        severity="high",
        execution_state="failed",
        retry_number=3,
        goal="root_cause",
    )


