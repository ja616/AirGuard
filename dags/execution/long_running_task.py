from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "long_running_task_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    # We use a 30s timeout so it fails in a reasonable time for the benchmark
    t1 = BashOperator(
        task_id='infinite_loop', 
        bash_command='sleep 120', 
        execution_timeout=timedelta(seconds=15)
    )
