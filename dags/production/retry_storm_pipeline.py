from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "retry_storm_pipeline",
    start_date=datetime(2026, 7, 1),
    schedule_interval="*/15 * * * *",
    catchup=False,
    default_args={"retries": 10, "retry_delay": timedelta(seconds=1)}
) as dag:
    storm = BashOperator(
        task_id='flaky_task', 
        bash_command='echo "Crashing randomly" && exit 1'
    )
