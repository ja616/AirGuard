from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Fails due to simulated AWS quota/cost.
# # Failure Mode: AWS API returns ResourceLimitExceeded.
# # Expected Evidence: CloudTrail denied event, CostExplorer spike.
# # Expected Root Cause: Instance type too large.
# # Expected Investigation Skill: InvestigateCostSpike
# # Expected Timeline: Start training -> Fails immediately -> Correlates to AWS billing.
# # Expected Operational Report: SageMaker ml.p4d instance exceeded budget.

with DAG(
    "sagemaker_cost_spike_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    def mock_sagemaker():
        raise ValueError('botocore.exceptions.ClientError: LimitExceededException')
    
    t1 = PythonOperator(task_id='train_model', python_callable=mock_sagemaker)
