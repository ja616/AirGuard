from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Simulates a hanging task (timeout).
# # Failure Mode: Task runs infinitely and hits execution_timeout.
# # Expected Evidence: AirflowTimeout in logs.
# # Expected Root Cause: Hanging DB query.
# # Expected Investigation Skill: InvestigateTimeout
# # Expected Timeline: Task Starts -> Hangs 2 hours -> Killed by scheduler.
# # Expected Operational Report: Deadlock or hanging query caused timeout.

with DAG(
    "long_running_task_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    t1 = BashOperator(task_id='infinite_loop', bash_command='sleep 7200', execution_timeout=timedelta(minutes=1))
