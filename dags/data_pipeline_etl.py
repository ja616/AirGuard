from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 5,
    'retry_delay': timedelta(seconds=5), # very short retry delay
}

with DAG(
    'data_pipeline_etl',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:
    
    def fail_task():
        print("Simulating a task failure to trigger a retry storm...")
        raise ValueError("Simulated connection timeout to database")
        
    t1 = PythonOperator(
        task_id='extract_data',
        python_callable=fail_task
    )
