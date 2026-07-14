from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Task succeeds but data quality checks fail.
# # Failure Mode: Downstream audit fails.
# # Expected Evidence: Row count 0.
# # Expected Root Cause: Upstream empty file.
# # Expected Investigation Skill: InvestigateDataQuality
# # Expected Timeline: Extract OK -> Load OK -> Audit Fails.
# # Expected Operational Report: Empty CSV uploaded by vendor.

with DAG(
    "silent_data_failure_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    t1 = BashOperator(task_id='extract', bash_command='echo OK')
    t2 = BashOperator(task_id='audit', bash_command='exit 1')
    t1 >> t2
