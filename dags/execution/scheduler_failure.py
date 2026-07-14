from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Validates behavior when Airflow scheduler goes down.
# # Failure Mode: Zombie tasks.
# # Expected Evidence: Task running but heartbeat missing.
# # Expected Root Cause: OOM on scheduler.
# # Expected Investigation Skill: InvestigateZombies
# # Expected Timeline: Task running -> Scheduler dies -> Zombie detected.
# # Expected Operational Report: Scheduler restart required.

with DAG(
    "scheduler_failure_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    t1 = BashOperator(task_id='zombie_candidate', bash_command='sleep 60')
