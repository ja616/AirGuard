from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def data_quality_check(**kwargs):
    # Simulating XCom silent data failure
    kwargs['ti'].xcom_push(key='row_count', value=0)
    kwargs['ti'].xcom_push(key='quality_check', value=False)
    # The task technically succeeds!

with DAG(
    "silent_data_failure_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    t1 = PythonOperator(task_id='extract_and_check_data', python_callable=data_quality_check)
