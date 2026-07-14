from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Simulates a task that continuously fails and triggers aggressive retries.
# # Failure Mode: Task fails repeatedly without backoff.
# # Expected Evidence: High try_number, repeated exceptions in logs.
# # Expected Root Cause: External dependency flake or bad data.
# # Expected Investigation Skill: InvestigateTaskRetries
# # Expected Timeline: Task Starts -> Fails -> Retries (x5) -> Permanent Failure
# # Expected Operational Report: Task X failed 5 times due to API 503.

with DAG(
    "retry_storm_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    def failing_task():
        raise ValueError('Upstream API returned 503 Service Unavailable')
    
    t1 = PythonOperator(task_id='failing_api_call', python_callable=failing_task)
