from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Simulates a DAG where half the tasks succeed, and half fail.
# # Failure Mode: DAG state is failed, but some data loaded.
# # Expected Evidence: Mixed task states.
# # Expected Root Cause: Partial network outage.
# # Expected Investigation Skill: InvestigatePartialFailure
# # Expected Timeline: Branch A OK -> Branch B Fails.
# # Expected Operational Report: Requires manual cleanup of Branch A.

with DAG(
    "partial_recovery_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    t1 = BashOperator(task_id='branch_a', bash_command='echo OK')
    t2 = BashOperator(task_id='branch_b', bash_command='exit 1')
    [t1, t2]
