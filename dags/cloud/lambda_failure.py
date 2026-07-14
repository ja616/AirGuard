from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Purpose: Triggers a real lambda that intentionally throws an error.
# # Failure Mode: Lambda times out or throws exception.
# # Expected Evidence: CloudWatch Logs show exception.
# # Expected Root Cause: Bad payload sent to Lambda.
# # Expected Investigation Skill: InvestigateLambda
# # Expected Timeline: Invoke -> 5xx Error -> Fail.
# # Expected Operational Report: Lambda function crashed with KeyError.

with DAG(
    "lambda_failure_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:

    t1 = BashOperator(task_id='invoke_lambda', bash_command='echo "Simulating Lambda failure" && exit 1')
