from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "sagemaker_cost_spike_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(
        task_id='sagemaker_train', 
        bash_command='echo "Training SageMaker model" && echo "Instance type changed to ml.p4d.24xlarge" && sleep 5 && exit 0'
    )
