from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "dependency_failure_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(task_id='upstream_task', bash_command='exit 1')
    t2 = BashOperator(task_id='downstream_task', bash_command='echo "Should not run"')
    t1 >> t2
