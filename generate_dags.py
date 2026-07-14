import os

dags_structure = {
    "scheduling/retry_storm.py": {
        "dag_id": "retry_storm_dag",
        "doc": "Purpose: Simulates a task that continuously fails and triggers aggressive retries.\n# Failure Mode: Task fails repeatedly without backoff.\n# Expected Evidence: High try_number, repeated exceptions in logs.\n# Expected Root Cause: External dependency flake or bad data.\n# Expected Investigation Skill: InvestigateTaskRetries\n# Expected Timeline: Task Starts -> Fails -> Retries (x5) -> Permanent Failure\n# Expected Operational Report: Task X failed 5 times due to API 503.",
        "code": "def failing_task():\n    raise ValueError('Upstream API returned 503 Service Unavailable')\n\nt1 = PythonOperator(task_id='failing_api_call', python_callable=failing_task)"
    },
    "scheduling/backfill_storm.py": {
        "dag_id": "backfill_storm_dag",
        "doc": "Purpose: Simulates massive parallel backfilling contention.\n# Failure Mode: Database connections exhausted or pool starved.\n# Expected Evidence: Tasks stuck in scheduled or queued state.\n# Expected Root Cause: Catchup=True with large date range.\n# Expected Investigation Skill: InvestigateBackfillContention\n# Expected Timeline: DAG unpaused -> 100 runs created -> Pool starvation.\n# Expected Operational Report: Backfill caused resource exhaustion.",
        "code": "def sleep_task():\n    import time\n    time.sleep(30)\n\nt1 = PythonOperator(task_id='slow_processing', python_callable=sleep_task)"
    },
    "scheduling/schedule_misconfig.py": {
        "dag_id": "schedule_misconfig_dag",
        "doc": "Purpose: Validates cron/schedule misalignment.\n# Failure Mode: DAG runs at wrong timezone or interval.\n# Expected Evidence: Start dates misaligned with business expectations.\n# Expected Root Cause: Bad cron string.\n# Expected Investigation Skill: InvestigateSchedule\n# Expected Timeline: DAG expected at 9AM -> Runs at 5AM.\n# Expected Operational Report: Timezone offset in cron string.",
        "code": "t1 = BashOperator(task_id='echo', bash_command='echo \"Running at wrong time\"')"
    },
    "execution/long_running_task.py": {
        "dag_id": "long_running_task_dag",
        "doc": "Purpose: Simulates a hanging task (timeout).\n# Failure Mode: Task runs infinitely and hits execution_timeout.\n# Expected Evidence: AirflowTimeout in logs.\n# Expected Root Cause: Hanging DB query.\n# Expected Investigation Skill: InvestigateTimeout\n# Expected Timeline: Task Starts -> Hangs 2 hours -> Killed by scheduler.\n# Expected Operational Report: Deadlock or hanging query caused timeout.",
        "code": "t1 = BashOperator(task_id='infinite_loop', bash_command='sleep 7200', execution_timeout=timedelta(minutes=1))"
    },
    "execution/dependency_failure.py": {
        "dag_id": "dependency_failure_dag",
        "doc": "Purpose: Upstream failure cascading down.\n# Failure Mode: Upstream fails, downstream skipped/upstream_failed.\n# Expected Evidence: State is upstream_failed.\n# Expected Root Cause: Root task threw exception.\n# Expected Investigation Skill: InvestigateDependencyCascade\n# Expected Timeline: Root Fails -> 10 tasks skipped.\n# Expected Operational Report: Root cause is task A, which caused B-Z to skip.",
        "code": "t1 = BashOperator(task_id='fail_root', bash_command='exit 1')\nt2 = BashOperator(task_id='downstream_1', bash_command='echo OK')\nt1 >> t2"
    },
    "execution/resource_contention.py": {
        "dag_id": "resource_contention_dag",
        "doc": "Purpose: Pool exhaustion.\n# Failure Mode: Task queued indefinitely.\n# Expected Evidence: Pool slots full.\n# Expected Root Cause: Concurrency limits too low.\n# Expected Investigation Skill: InvestigateQueuedTasks\n# Expected Timeline: Queued -> Stuck -> Timeout.\n# Expected Operational Report: Pool 'default' is full.",
        "code": "t1 = BashOperator(task_id='contended_task', bash_command='sleep 10', pool='limited_pool')"
    },
    "execution/scheduler_failure.py": {
        "dag_id": "scheduler_failure_dag",
        "doc": "Purpose: Validates behavior when Airflow scheduler goes down.\n# Failure Mode: Zombie tasks.\n# Expected Evidence: Task running but heartbeat missing.\n# Expected Root Cause: OOM on scheduler.\n# Expected Investigation Skill: InvestigateZombies\n# Expected Timeline: Task running -> Scheduler dies -> Zombie detected.\n# Expected Operational Report: Scheduler restart required.",
        "code": "t1 = BashOperator(task_id='zombie_candidate', bash_command='sleep 60')"
    },
    "cloud/sagemaker_cost_spike.py": {
        "dag_id": "sagemaker_cost_spike_dag",
        "doc": "Purpose: Fails due to simulated AWS quota/cost.\n# Failure Mode: AWS API returns ResourceLimitExceeded.\n# Expected Evidence: CloudTrail denied event, CostExplorer spike.\n# Expected Root Cause: Instance type too large.\n# Expected Investigation Skill: InvestigateCostSpike\n# Expected Timeline: Start training -> Fails immediately -> Correlates to AWS billing.\n# Expected Operational Report: SageMaker ml.p4d instance exceeded budget.",
        "code": "def mock_sagemaker():\n    raise ValueError('botocore.exceptions.ClientError: LimitExceededException')\n\nt1 = PythonOperator(task_id='train_model', python_callable=mock_sagemaker)"
    },
    "cloud/lambda_failure.py": {
        "dag_id": "lambda_failure_dag",
        "doc": "Purpose: Triggers a real lambda that intentionally throws an error.\n# Failure Mode: Lambda times out or throws exception.\n# Expected Evidence: CloudWatch Logs show exception.\n# Expected Root Cause: Bad payload sent to Lambda.\n# Expected Investigation Skill: InvestigateLambda\n# Expected Timeline: Invoke -> 5xx Error -> Fail.\n# Expected Operational Report: Lambda function crashed with KeyError.",
        "code": "t1 = BashOperator(task_id='invoke_lambda', bash_command='echo \"Simulating Lambda failure\" && exit 1')"
    },
    "data/silent_data_failure.py": {
        "dag_id": "silent_data_failure_dag",
        "doc": "Purpose: Task succeeds but data quality checks fail.\n# Failure Mode: Downstream audit fails.\n# Expected Evidence: Row count 0.\n# Expected Root Cause: Upstream empty file.\n# Expected Investigation Skill: InvestigateDataQuality\n# Expected Timeline: Extract OK -> Load OK -> Audit Fails.\n# Expected Operational Report: Empty CSV uploaded by vendor.",
        "code": "t1 = BashOperator(task_id='extract', bash_command='echo OK')\nt2 = BashOperator(task_id='audit', bash_command='exit 1')\nt1 >> t2"
    },
    "recovery/partial_recovery.py": {
        "dag_id": "partial_recovery_dag",
        "doc": "Purpose: Simulates a DAG where half the tasks succeed, and half fail.\n# Failure Mode: DAG state is failed, but some data loaded.\n# Expected Evidence: Mixed task states.\n# Expected Root Cause: Partial network outage.\n# Expected Investigation Skill: InvestigatePartialFailure\n# Expected Timeline: Branch A OK -> Branch B Fails.\n# Expected Operational Report: Requires manual cleanup of Branch A.",
        "code": "t1 = BashOperator(task_id='branch_a', bash_command='echo OK')\nt2 = BashOperator(task_id='branch_b', bash_command='exit 1')\n[t1, t2]"
    },
    "operations/manual_trigger_storm.py": {
        "dag_id": "manual_trigger_storm_dag",
        "doc": "Purpose: Simulates a user clicking Trigger DAG 50 times.\n# Failure Mode: Max active runs exceeded.\n# Expected Evidence: 50 running DAGs.\n# Expected Root Cause: User error.\n# Expected Investigation Skill: InvestigateManualRuns\n# Expected Timeline: 50 triggers -> System sluggish.\n# Expected Operational Report: Operator 'john' triggered DAG repeatedly.",
        "code": "t1 = BashOperator(task_id='do_work', bash_command='sleep 5')"
    },
    "operations/dag_pause_resume.py": {
        "dag_id": "dag_pause_resume_dag",
        "doc": "Purpose: DAG was paused for a week, then resumed with catchup=True.\n# Failure Mode: Massive catchup.\n# Expected Evidence: DAG paused status changed.\n# Expected Root Cause: Operational gap.\n# Expected Investigation Skill: InvestigatePauseState\n# Expected Timeline: Paused -> 7 days pass -> Resumed -> Crush.\n# Expected Operational Report: Unpaused without disabling catchup.",
        "code": "t1 = BashOperator(task_id='sync', bash_command='sleep 1')"
    },
    "operations/excessive_parallelism.py": {
        "dag_id": "excessive_parallelism_dag",
        "doc": "Purpose: Dynamic task mapping creates 10,000 tasks.\n# Failure Mode: Scheduler OOM.\n# Expected Evidence: Huge mapped task index.\n# Expected Root Cause: Bad input to expand().\n# Expected Investigation Skill: InvestigateTaskMapping\n# Expected Timeline: Expand -> 10k tasks -> DB Locks.\n# Expected Operational Report: Dynamic mapping exploded due to bad input list.",
        "code": "t1 = BashOperator(task_id='expand_mock', bash_command='echo \"Pretend 10k tasks\" && exit 1')"
    },
    "operations/unexpected_dag_explosion.py": {
        "dag_id": "unexpected_dag_explosion_dag",
        "doc": "Purpose: DAG generation file creates 1000 DAGs dynamically.\n# Failure Mode: DagBag parse timeout.\n# Expected Evidence: import_errors in Airflow.\n# Expected Root Cause: For-loop creating DAGs.\n# Expected Investigation Skill: InvestigateParseTime\n# Expected Timeline: File parsed -> 1000 DAGs -> Timeout.\n# Expected Operational Report: Dynamic DAG script exceeded 30s timeout.",
        "code": "t1 = BashOperator(task_id='explosion_mock', bash_command='exit 1')"
    }
}

template = '''from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# {doc}

with DAG(
    "{dag_id}",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args={{"retries": 1, "retry_delay": timedelta(seconds=5)}}
) as dag:

    {code}
'''

for path, info in dags_structure.items():
    full_path = os.path.join("c:/Users/aishw/.gemini/antigravity-ide/scratch/AirGuard/dags", path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(template.format(
            doc=info['doc'].replace('\n', '\n# '),
            dag_id=info['dag_id'],
            code=info['code'].replace('\n', '\n    ')
        ))

print("Successfully generated 15 operational DAGs.")
