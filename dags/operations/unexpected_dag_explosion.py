from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "unexpected_dag_explosion_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(task_id='failing_task', bash_command='exit 1')
