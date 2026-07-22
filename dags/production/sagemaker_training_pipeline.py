from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "sagemaker_training_pipeline",
    start_date=datetime(2026, 7, 1),
    schedule_interval="@weekly",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    train = BashOperator(
        task_id='start_training_job', 
        bash_command='echo "Starting SageMaker job..." && echo "Cost Alert: p4d.24xlarge instance provisioning"'
    )
