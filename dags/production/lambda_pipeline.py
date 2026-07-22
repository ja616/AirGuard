from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "lambda_pipeline",
    start_date=datetime(2026, 7, 1),
    schedule_interval="@hourly",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=10)}
) as dag:
    invoke = BashOperator(
        task_id='invoke_lambda', 
        bash_command='echo "Lambda" && echo "Calling Lambda AWS... Timeout!" && exit 1'
    )
