from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "backfill_storm_dag",
    start_date=datetime(2025, 1, 1), # Old start date, catchup=True!
    schedule_interval="@daily",
    catchup=True,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(task_id='catchup_task', bash_command='sleep 1')
