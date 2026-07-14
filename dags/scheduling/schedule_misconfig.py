from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Validates cron/schedule misalignment.
# # Failure Mode: DAG runs at wrong timezone or interval.
# # Expected Evidence: Start dates misaligned with business expectations.
# # Expected Root Cause: Bad cron string.
# # Expected Investigation Skill: InvestigateSchedule
# # Expected Timeline: DAG expected at 9AM -> Runs at 5AM.
# # Expected Operational Report: Timezone offset in cron string.

with DAG(
    "schedule_misconfig_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    t1 = BashOperator(task_id='echo', bash_command='echo "Running at wrong time"')
