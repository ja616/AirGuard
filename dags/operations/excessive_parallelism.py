from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Dynamic task mapping creates 10,000 tasks.
# # Failure Mode: Scheduler OOM.
# # Expected Evidence: Huge mapped task index.
# # Expected Root Cause: Bad input to expand().
# # Expected Investigation Skill: InvestigateTaskMapping
# # Expected Timeline: Expand -> 10k tasks -> DB Locks.
# # Expected Operational Report: Dynamic mapping exploded due to bad input list.

with DAG(
    "excessive_parallelism_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    t1 = BashOperator(task_id='expand_mock', bash_command='echo "Pretend 10k tasks" && exit 1')
