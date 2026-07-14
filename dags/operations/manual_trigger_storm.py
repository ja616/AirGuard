from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Simulates a user clicking Trigger DAG 50 times.
# # Failure Mode: Max active runs exceeded.
# # Expected Evidence: 50 running DAGs.
# # Expected Root Cause: User error.
# # Expected Investigation Skill: InvestigateManualRuns
# # Expected Timeline: 50 triggers -> System sluggish.
# # Expected Operational Report: Operator 'john' triggered DAG repeatedly.

with DAG(
    "manual_trigger_storm_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    t1 = BashOperator(task_id='do_work', bash_command='sleep 5')
