from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "schedule_misconfig_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="*/1 * * * *", # Every minute (misconfig!)
    catchup=False,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(task_id='frequent_task', bash_command='echo "Running too often"')
