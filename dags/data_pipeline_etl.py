from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from airguard_callbacks import notify_airguard_failure, notify_airguard_retry

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 3,
    'retry_delay': timedelta(seconds=10),
    # ── AirGuard: auto-trigger investigation on failure / retry ──────────────
    'on_failure_callback': notify_airguard_failure,
    'on_retry_callback': notify_airguard_retry,
}

with DAG(
    'data_pipeline_etl',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=['etl', 'production'],
) as dag:

    def fail_task(**context):
        """Simulates a connection timeout to trigger the retry storm scenario."""
        print("Attempting to connect to upstream database...")
        print("ERROR: Connection timeout after 30s — upstream database is unreachable.")
        raise ValueError("Connection timeout to upstream database")

    extract_raw_data = PythonOperator(
        task_id='extract_raw_data',
        python_callable=fail_task,
    )
