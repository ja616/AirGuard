from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "timeout_pipeline",
    start_date=datetime(2026, 7, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=10)}
) as dag:
    long_task = BashOperator(
        task_id='long_running_db_query', 
        bash_command='sleep 120 && echo "Done"'
    )
