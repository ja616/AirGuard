from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "permission_pipeline",
    start_date=datetime(2026, 7, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1}
) as dag:
    task = BashOperator(
        task_id='assume_role', 
        bash_command='echo "AccessDenied: Not authorized to perform sts:AssumeRole" && exit 1'
    )
