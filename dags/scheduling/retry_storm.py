from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def failing_task():
    raise ValueError('Upstream API returned 503 Service Unavailable')

with DAG(
    "retry_storm_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 5, "retry_delay": timedelta(seconds=2)}
) as dag:
    t1 = PythonOperator(task_id='failing_api_call', python_callable=failing_task)
