from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Upstream failure cascading down.
# # Failure Mode: Upstream fails, downstream skipped/upstream_failed.
# # Expected Evidence: State is upstream_failed.
# # Expected Root Cause: Root task threw exception.
# # Expected Investigation Skill: InvestigateDependencyCascade
# # Expected Timeline: Root Fails -> 10 tasks skipped.
# # Expected Operational Report: Root cause is task A, which caused B-Z to skip.

with DAG(
    "dependency_failure_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    t1 = BashOperator(task_id='fail_root', bash_command='exit 1')
    t2 = BashOperator(task_id='downstream_1', bash_command='echo OK')
    t1 >> t2
