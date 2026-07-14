from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: DAG was paused for a week, then resumed with catchup=True.
# # Failure Mode: Massive catchup.
# # Expected Evidence: DAG paused status changed.
# # Expected Root Cause: Operational gap.
# # Expected Investigation Skill: InvestigatePauseState
# # Expected Timeline: Paused -> 7 days pass -> Resumed -> Crush.
# # Expected Operational Report: Unpaused without disabling catchup.

with DAG(
    "dag_pause_resume_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    t1 = BashOperator(task_id='sync', bash_command='sleep 1')
