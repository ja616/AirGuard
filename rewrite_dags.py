import os

dags_dir = "dags"

dags_content = {
    "cloud/lambda_failure.py": """from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "lambda_failure_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)}
) as dag:
    t1 = BashOperator(
        task_id='invoke_lambda', 
        bash_command='echo "Executing Lambda function" && echo "Lambda" && echo "AWS Error: Request throttled" && exit 1'
    )
""",
    "cloud/sagemaker_cost_spike.py": """from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "sagemaker_cost_spike_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(
        task_id='sagemaker_train', 
        bash_command='echo "Training SageMaker model" && echo "Instance type changed to ml.p4d.24xlarge" && sleep 5 && exit 0'
    )
""",
    "data/silent_data_failure.py": """from airflow import DAG
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
""",
    "execution/dependency_failure.py": """from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "dependency_failure_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(task_id='upstream_task', bash_command='exit 1')
    t2 = BashOperator(task_id='downstream_task', bash_command='echo "Should not run"')
    t1 >> t2
""",
    "execution/long_running_task.py": """from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "long_running_task_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    # We use a 30s timeout so it fails in a reasonable time for the benchmark
    t1 = BashOperator(
        task_id='infinite_loop', 
        bash_command='sleep 120', 
        execution_timeout=timedelta(seconds=15)
    )
""",
    "execution/resource_contention.py": """from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "resource_contention_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    # Use a specific pool that we assume has 1 slot
    t1 = BashOperator(task_id='contended_task_1', bash_command='sleep 10', pool='limited_pool')
    t2 = BashOperator(task_id='contended_task_2', bash_command='sleep 10', pool='limited_pool')
""",
    "execution/scheduler_failure.py": """from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "scheduler_failure_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    # A DAG simulating a stuck queue, which we'll handle from the client side by artificially breaking the scheduler
    t1 = BashOperator(task_id='stuck_task', bash_command='echo "Waiting for scheduler"')
""",
    "operations/dag_pause_resume.py": """from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "dag_pause_resume_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(task_id='test_task', bash_command='echo "Running"')
""",
    "operations/excessive_parallelism.py": """from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "excessive_parallelism_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(task_id='wide_task', bash_command='echo "Wide mapping"')
    # We'll simulate 10k task instances in the mock/client layer if needed
""",
    "operations/manual_trigger_storm.py": """from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "manual_trigger_storm_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(task_id='manual_task', bash_command='echo "Triggered manually"')
""",
    "operations/unexpected_dag_explosion.py": """from airflow import DAG
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
""",
    "recovery/partial_recovery.py": """from airflow import DAG
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
""",
    "scheduling/backfill_storm.py": """from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "backfill_storm_dag",
    start_date=datetime(2025, 1, 1), # Old start date, catchup=True!
    schedule_interval="@daily",
    catchup=True,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(task_id='catchup_task', bash_command='sleep 1')
""",
    "scheduling/retry_storm.py": """from airflow import DAG
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
""",
    "scheduling/schedule_misconfig.py": """from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    "schedule_misconfig_dag",
    start_date=datetime(2026, 1, 1),
    schedule_interval="*/1 * * * *", # Every minute (misconfig!)
    catchup=False,
    default_args={"retries": 0}
) as dag:
    t1 = BashOperator(task_id='frequent_task', bash_command='echo "Running too often"')
"""
}

for rel_path, content in dags_content.items():
    full_path = os.path.join(dags_dir, rel_path)
    with open(full_path, "w") as f:
        f.write(content)
    print(f"Updated {full_path}")

print("All DAGs updated!")
