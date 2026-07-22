from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "scheduler_pipeline",
    start_date=datetime(2026, 7, 1),
    schedule_interval="@hourly",
    catchup=False,
    default_args={"retries": 1}
) as dag:
    task = BashOperator(
        task_id='heartbeat_check', 
        bash_command='echo "Scheduler heartbeat check"'
    )
