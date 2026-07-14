from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Pool exhaustion.
# # Failure Mode: Task queued indefinitely.
# # Expected Evidence: Pool slots full.
# # Expected Root Cause: Concurrency limits too low.
# # Expected Investigation Skill: InvestigateQueuedTasks
# # Expected Timeline: Queued -> Stuck -> Timeout.
# # Expected Operational Report: Pool 'default' is full.

with DAG(
    "resource_contention_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    t1 = BashOperator(task_id='contended_task', bash_command='sleep 10', pool='limited_pool')
