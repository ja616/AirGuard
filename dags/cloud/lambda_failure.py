from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "lambda_failure_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:
    t1 = BashOperator(
        task_id='invoke_lambda', 
        bash_command='echo "Executing Lambda function" && echo "Lambda" && echo "AWS Error: Request throttled" && exit 1'
    )
