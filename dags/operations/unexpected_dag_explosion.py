from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: DAG generation file creates 1000 DAGs dynamically.
# # Failure Mode: DagBag parse timeout.
# # Expected Evidence: import_errors in Airflow.
# # Expected Root Cause: For-loop creating DAGs.
# # Expected Investigation Skill: InvestigateParseTime
# # Expected Timeline: File parsed -> 1000 DAGs -> Timeout.
# # Expected Operational Report: Dynamic DAG script exceeded 30s timeout.

with DAG(
    "unexpected_dag_explosion_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    t1 = BashOperator(task_id='explosion_mock', bash_command='exit 1')
