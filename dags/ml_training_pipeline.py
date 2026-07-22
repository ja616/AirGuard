from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# SCENARIO: The Phantom Retraining Storm
# Someone accidentally set the schedule interval to '* * * * *' (every minute)
# instead of '@daily'. Catchup is True. 
# Result: 360 successful SageMaker training jobs spawn in 6 hours, spiking AWS costs.

default_args = {
    'owner': 'ml_team',
    'depends_on_past': False,
    'start_date': datetime.now() - timedelta(hours=6),
    'retries': 0,
}

dag = DAG(
    'ml_training_pipeline',
    default_args=default_args,
    description='Daily ML Training Pipeline',
    schedule_interval='* * * * *',  # The BUG: Every minute instead of daily
    catchup=True,
    max_active_runs=15, # Allows rapid backfilling
    tags=['ml', 'sagemaker', 'production']
)

# A fake SageMaker training task that always succeeds
trigger_sagemaker_training = BashOperator(
    task_id='trigger_sagemaker_training',
    bash_command='echo "Submitting SageMaker Training Job... Job Completed Successfully." && sleep 2',
    dag=dag,
)

trigger_sagemaker_training
