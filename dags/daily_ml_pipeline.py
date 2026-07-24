from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

from airguard_callbacks import notify_airguard_failure, notify_airguard_retry

# SCENARIO: The SageMaker Timeout Loop
# This DAG simulates an ML pipeline where the training task gets stuck,
# times out, and retries multiple times. This leaves orphaned SageMaker
# jobs running in AWS (which the user can show in their real AWS console),
# while Airflow eventually fails the task after 3 retries.

default_args = {
    'owner': 'ml_team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'retries': 3,
    'retry_delay': timedelta(seconds=10),  # Fast retry for demo purposes
    # ── AirGuard: auto-trigger investigation on failure / retry ──────────────
    'on_failure_callback': notify_airguard_failure,
    'on_retry_callback': notify_airguard_retry,
}

dag = DAG(
    'daily_ml_pipeline',
    default_args=default_args,
    description='Daily ML Pipeline',
    schedule_interval='@daily',
    catchup=False,
    tags=['ml', 'sagemaker', 'production'],
    # DAG-level failure callback (fires when the whole run is marked failed)
    on_failure_callback=None,   # task-level callbacks cover this scenario
)

extract_data = BashOperator(
    task_id='extract_data',
    bash_command='echo "Extracting data from Redshift..." && sleep 2',
    dag=dag,
)

validate_dataset = BashOperator(
    task_id='validate_dataset',
    bash_command='echo "Validating schema and data quality..." && sleep 2',
    dag=dag,
)

feature_engineering = BashOperator(
    task_id='feature_engineering',
    bash_command='echo "Computing features..." && sleep 2',
    dag=dag,
)

# The failing task.
# It prints logs indicating a timeout so AirGuard's evidence collection
# picks up the "SageMaker API Timeout" keyword when reading the Airflow logs.
train_sagemaker_model = BashOperator(
    task_id='train_sagemaker_model',
    bash_command='''
        echo "Submitting SageMaker Training Job: sagemaker-xgboost-2026-07-22"
        echo "Waiting for job to complete..."
        sleep 5
        echo "Error: SageMaker API Timeout. The job is still running in AWS, but the Airflow operator timed out after 30 minutes."
        exit 1
    ''',
    dag=dag,
)

model_evaluation = BashOperator(
    task_id='model_evaluation',
    bash_command='echo "Evaluating model metrics..." && sleep 2',
    dag=dag,
)

register_model = BashOperator(
    task_id='register_model',
    bash_command='echo "Registering model to Model Registry..." && sleep 2',
    dag=dag,
)

# Set dependencies
extract_data >> validate_dataset >> feature_engineering >> train_sagemaker_model >> model_evaluation >> register_model
