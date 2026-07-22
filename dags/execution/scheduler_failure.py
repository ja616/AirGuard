from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "scheduler_failure_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    # A DAG simulating a stuck queue, which we'll handle from the client side by artificially breaking the scheduler
    t1 = BashOperator(task_id='stuck_task', bash_command='echo "Waiting for scheduler"')
