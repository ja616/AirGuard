"""
Tool Schemas — AirGuard
========================
Single source of truth for tool names and their human-readable descriptions.

These descriptions are used when registering tools with the AgentCore Harness
as inline function definitions. Keeping them here (rather than in the adapter)
means adding a new tool requires editing only two files:
  1. tools/registry.py  — implement the function + add to TOOL_REGISTRY
  2. tools/schemas.py   — add the description here

The AgentCoreAdapter reads from this module; it never hardcodes descriptions.
"""

TOOL_DESCRIPTIONS: dict[str, str] = {
    # ── Airflow ───────────────────────────────────────────────────────────────
    "get_scheduler_health":         "Check Airflow scheduler and metadatabase health status.",
    "get_scheduler_heartbeat":      "Measure scheduler heartbeat lag in seconds.",
    "get_airflow_version":          "Retrieve the current Airflow version string.",
    "get_airflow_config":           "Retrieve relevant Airflow configuration values.",
    "get_dag_runs":                 "Retrieve the last 10 DAG run records including state and run type.",
    "get_dag_details":              "Retrieve DAG metadata including schedule, concurrency, and tags.",
    "get_dag_run_by_id":            "Retrieve a specific DAG run by its run ID.",
    "get_all_dags":                 "List all DAGs and their active/paused state.",
    "get_task_instances":           "Retrieve task instance states for the latest DAG run.",
    "get_failed_task_logs":         "Retrieve logs from the most recently failed task instance across all retry attempts.",
    "get_task_xcoms":               "Retrieve XCom values produced by tasks in the latest DAG run.",
    "get_pool_stats":               "Retrieve Airflow pool slot usage and queue depth.",
    "get_import_errors":            "Check Airflow for DAG import or parsing errors.",
    "detect_retry_storm":           "Detect retry storm patterns across recent DAG runs.",
    "detect_cascade_failure":       "Detect cross-DAG cascade failure patterns.",
    # ── CloudWatch / Lambda ───────────────────────────────────────────────────
    "get_lambda_errors":            "Retrieve Lambda function error count from CloudWatch.",
    "get_lambda_duration":          "Retrieve Lambda function average duration from CloudWatch.",
    "get_lambda_throttles":         "Retrieve Lambda throttle count from CloudWatch.",
    "get_lambda_invocations":       "Retrieve Lambda invocation count from CloudWatch.",
    # ── CloudTrail ────────────────────────────────────────────────────────────
    "get_lambda_invocation_events": "Retrieve CloudTrail events for Lambda invocations.",
    "get_iam_policy_changes":       "Retrieve recent IAM policy change events from CloudTrail.",
    "get_resource_config_changes":  "Retrieve recent AWS resource configuration changes from CloudTrail.",
    # ── Redis ─────────────────────────────────────────────────────────────────
    "get_redis_health":             "Check Redis connectivity and health.",
    "get_redis_queue_depth":        "Get the number of tasks queued in Redis.",
    # ── Postgres ─────────────────────────────────────────────────────────────
    "get_postgres_connection_count":"Count active Postgres connections.",
    "get_postgres_slow_queries":    "Retrieve slow queries from Postgres pg_stat_activity.",
    # ── Cost Explorer ─────────────────────────────────────────────────────────
    "get_lambda_cost_delta":        "Estimate Lambda cost change from AWS Cost Explorer.",
}
