from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "resource_contention_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    # Use a specific pool that we assume has 1 slot
    t1 = BashOperator(task_id='contended_task_1', bash_command='sleep 10', pool='limited_pool')
    t2 = BashOperator(task_id='contended_task_2', bash_command='sleep 10', pool='limited_pool')
