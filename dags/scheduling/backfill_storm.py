from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Simulates massive parallel backfilling contention.
# # Failure Mode: Database connections exhausted or pool starved.
# # Expected Evidence: Tasks stuck in scheduled or queued state.
# # Expected Root Cause: Catchup=True with large date range.
# # Expected Investigation Skill: InvestigateBackfillContention
# # Expected Timeline: DAG unpaused -> 100 runs created -> Pool starvation.
# # Expected Operational Report: Backfill caused resource exhaustion.

with DAG(
    "backfill_storm_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    def sleep_task():
        import time
        time.sleep(30)
    
    t1 = PythonOperator(task_id='slow_processing', python_callable=sleep_task)
