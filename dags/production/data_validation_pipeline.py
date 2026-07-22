from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "data_validation_pipeline",
    start_date=datetime(2026, 7, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1}
) as dag:
    validate = BashOperator(
        task_id='validate_data', 
        bash_command='echo "Data validation failed: 0 rows returned" && exit 1'
    )
