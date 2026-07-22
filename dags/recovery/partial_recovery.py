from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import random

def flaky_task():
    # Will sometimes succeed, sometimes fail, so over retries it looks like partial recovery
    if random.random() < 0.5:
        raise ValueError("Flaky failure")

with DAG(
    "partial_recovery_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 3, "retry_delay": timedelta(seconds=2)}
) as dag:
    t1 = PythonOperator(task_id='flaky_task', python_callable=flaky_task)
    t2 = PythonOperator(task_id='stable_task', python_callable=lambda: print("Stable"))
