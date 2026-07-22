from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "excessive_parallelism_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(task_id='wide_task', bash_command='echo "Wide mapping"')
    # We'll simulate 10k task instances in the mock/client layer if needed
