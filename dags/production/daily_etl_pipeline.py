from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "daily_etl_pipeline",
    start_date=datetime(2026, 7, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=30)}
) as dag:
    extract = BashOperator(
        task_id='extract_data', 
        bash_command='echo "Extracting data from Postgres"'
    )
    transform = BashOperator(
        task_id='transform_data', 
        bash_command='echo "Transforming data..."'
    )
    load = BashOperator(
        task_id='load_data', 
        bash_command='echo "Loading data to Redshift"'
    )
    extract >> transform >> load
