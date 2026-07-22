import requests
import json

BASE = "http://localhost:8000"
TOKEN = "airguard-local-dev-secret-2026"
PASS = 0
FAIL = 0

def check(label, r, expected_status=200):
    global PASS, FAIL
    status = "PASS" if r.status_code == expected_status else "FAIL"
    if status == "PASS":
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{status}] {label} -> HTTP {r.status_code}")
    if status == "FAIL":
        print(f"         Body: {r.text[:300]}")
    return r

print("=" * 60)
print("TEST 1: Structured IncidentContext payload")
print("=" * 60)
r1 = requests.post(f"{BASE}/api/v1/investigations/", json={
    "dag_id": "data_pipeline_etl",
    "failed_node_id": "extract_raw_data",
    "severity": "high",
    "execution_state": "failed",
    "retry_number": 3,
    "investigation_goal": "root_cause",
    "environment": "prod",
})
r1 = check("Structured IncidentContext", r1)
d1 = r1.json()
print(f"  inv_id={d1.get('id')} | state={d1.get('state')}")

print()
print("=" * 60)
print("TEST 2: Legacy user_query payload")
print("=" * 60)
r2 = requests.post(f"{BASE}/api/v1/investigations/", json={
    "dag_id": "data_pipeline_etl",
    "user_query": "Tasks are failing with Lambda throttles",
})
r2 = check("Legacy user_query", r2)
d2 = r2.json()
print(f"  inv_id={d2.get('id')} | state={d2.get('state')}")

print()
print("=" * 60)
print("TEST 3: Airflow webhook — task_failure (valid token)")
print("=" * 60)
r3 = requests.post(
    f"{BASE}/api/v1/airflow/webhook",
    json={
        "callback_type": "task_failure",
        "dag_id": "data_pipeline_etl",
        "run_id": "scheduled__2026-07-21T06:00:00+00:00",
        "task_id": "extract_raw_data",
        "try_number": 3,
        "state": "failed",
        "exception": "AirflowException: upstream connection refused",
        "environment": "prod",
    },
    headers={"X-AirGuard-Token": TOKEN},
)
r3 = check("Webhook task_failure (valid token)", r3)
d3 = r3.json()
print(f"  inv_id={d3.get('investigation_id')} | severity={d3.get('severity')} | cb_type={d3.get('callback_type')}")

print()
print("=" * 60)
print("TEST 4: Webhook — wrong token (expect 401)")
print("=" * 60)
r4 = requests.post(
    f"{BASE}/api/v1/airflow/webhook",
    json={"callback_type": "task_failure", "dag_id": "test_dag"},
    headers={"X-AirGuard-Token": "wrong-token"},
)
check("Webhook bad token", r4, expected_status=401)

print()
print("=" * 60)
print("TEST 5: Webhook — sla_miss callback")
print("=" * 60)
r5 = requests.post(
    f"{BASE}/api/v1/airflow/webhook",
    json={
        "callback_type": "sla_miss",
        "dag_id": "data_pipeline_etl",
        "environment": "prod",
        "investigation_goal": "impact_analysis",
    },
    headers={"X-AirGuard-Token": TOKEN},
)
r5 = check("Webhook sla_miss", r5)
d5 = r5.json()
print(f"  inv_id={d5.get('investigation_id')} | severity={d5.get('severity')} | cb_type={d5.get('callback_type')}")

print()
print("=" * 60)
print("TEST 6: Webhook — dag_failure callback")
print("=" * 60)
r6 = requests.post(
    f"{BASE}/api/v1/airflow/webhook",
    json={
        "callback_type": "dag_failure",
        "dag_id": "data_pipeline_etl",
        "run_id": "manual__2026-07-21T10:00:00",
        "environment": "prod",
        "severity": "critical",
    },
    headers={"X-AirGuard-Token": TOKEN},
)
r6 = check("Webhook dag_failure", r6)
d6 = r6.json()
print(f"  inv_id={d6.get('investigation_id')} | severity={d6.get('severity')}")

print()
print("=" * 60)
print(f"Results: {PASS} passed, {FAIL} failed")
print("=" * 60)
