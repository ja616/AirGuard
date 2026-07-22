"""
Normalization Stage
====================
Extracts boolean/numeric signals from raw Evidence objects.
Each signal key must match at least one classification_signal in taxonomy/registry.py.
"""
from typing import List
from backend.investigation.models import NormalizedEvidenceBundle
from backend.evidence.models import Evidence


def run(evidence: List[Evidence]) -> NormalizedEvidenceBundle:
    signals = {}
    evidence_ids = []
    sources = set()

    for e in evidence:
        evidence_ids.append(e.id)
        sources.add(e.source)
        p = e.normalized_payload

        # ── Airflow Scheduler ────────────────────────────────────────────────
        if e.source == "airflow_scheduler_health":
            if p.get("status") not in ("healthy", "healthy"):
                signals["scheduler_state_unhealthy"] = True
            if p.get("db_status") != "healthy":
                signals["scheduler_db_unhealthy"] = True

        elif e.source == "airflow_scheduler_heartbeat":
            if p.get("is_stale"):
                signals["scheduler_state_unhealthy"] = True
                signals["pending_tasks_age_high"] = True

        # ── Airflow DAG Runs ─────────────────────────────────────────────────
        elif e.source == "airflow_dag_runs":
            runs = p.get("runs", [])
            if p.get("manual_count", 0) >= 5:
                signals["manual_trigger_count_high"] = True
                signals["triggered_by_user"] = True
            if p.get("backfill_count", 0) >= 3:
                signals["backfill_run_count_high"] = True
            # Multiple failed runs → persistent failure
            if p.get("failed_count", 0) >= 2:
                signals["previous_run_failed"] = True

        # ── Airflow DAG Details ──────────────────────────────────────────────
        elif e.source == "airflow_dag_details":
            if p.get("is_paused"):
                signals["dag_paused_changed"] = True

        # ── Airflow Task Instances ───────────────────────────────────────────
        elif e.source == "airflow_task_instances":
            tasks = p.get("tasks", [])
            if p.get("failed_count", 0) > 0:
                signals["task_state_failed"] = True
                max_try = p.get("max_try_number", 1)
                if max_try > 4:
                    signals["task_retry_count_high"] = True
                else:
                    signals["task_retry_count_low"] = True
            if p.get("upstream_failed_count", 0) > 0 and p.get("failed_count", 0) > 0:
                signals["upstream_task_failed"] = True
                signals["downstream_state_upstream_failed"] = True
            if p.get("running_count", 0) > 100:
                signals["concurrent_tasks_maxed"] = True
                signals["concurrent_tasks_high"] = True
            if p.get("success_count", 0) > 0 and p.get("failed_count", 0) > 0:
                signals["some_tasks_success"] = True
                signals["some_tasks_failed"] = True
                signals["previous_run_failed"] = True
            # Pool saturation indicator from task queueing
            queued_count = sum(1 for t in tasks if t.get("state") == "queued")
            if queued_count > 10:
                signals["pool_queued_slots_high"] = True
                signals["concurrent_tasks_high"] = True

        # ── Airflow Task Logs ────────────────────────────────────────────────
        elif e.source == "airflow_task_logs":
            if p.get("contains_lambda"):
                signals["task_logs_contain_lambda"] = True
            if p.get("contains_timeout"):
                signals["task_state_running_timeout"] = True
                signals["task_duration_high"] = True
            if p.get("contains_permission_error"):
                signals["task_logs_contain_permission_error"] = True
            if p.get("contains_oom_kill"):
                signals["task_oom_killed"] = True

        # ── Airflow XComs ────────────────────────────────────────────────────
        elif e.source == "airflow_xcoms":
            if p.get("quality_check_failed"):
                signals["xcom_quality_check_failed"] = True
            if p.get("row_count_zero"):
                signals["xcom_row_count_zero"] = True
            if p.get("xcoms"):
                signals["task_state_success"] = True

        # ── Airflow Pool Stats ───────────────────────────────────────────────
        elif e.source == "airflow_pool_stats":
            if p.get("pool_saturated"):
                signals["pool_queued_slots_high"] = True
                signals["concurrent_tasks_high"] = True
            if p.get("queued_slots", 0) > 20:
                signals["queued_tasks_high"] = True

        # ── Import Errors ────────────────────────────────────────────────────
        elif e.source == "airflow_import_errors":
            if p.get("has_import_errors"):
                signals["dag_import_error"] = True
            if p.get("dag_specific_errors"):
                signals["task_state_failed"] = True

        # ── Retry Analysis ───────────────────────────────────────────────────
        elif e.source == "airflow_retry_analysis":
            if p.get("retry_storm_detected"):
                signals["task_retry_count_high"] = True
            if p.get("retry_interval_short"):
                signals["retry_interval_short"] = True
            if p.get("rapid_runs"):
                signals["manual_trigger_count_high"] = True

        # ── Cascade Analysis ─────────────────────────────────────────────────
        elif e.source == "airflow_cascade_analysis":
            if p.get("cascade_failure_detected"):
                signals["upstream_task_failed"] = True
                signals["downstream_state_upstream_failed"] = True

        # ── CloudWatch Lambda ────────────────────────────────────────────────
        elif e.source == "cloudwatch_lambda_errors":
            if p.get("lambda_errors_present"):
                signals["aws_lambda_error_count_high"] = True
                signals["task_logs_contain_lambda"] = True

        elif e.source == "cloudwatch_lambda_duration":
            if p.get("lambda_near_timeout"):
                signals["task_duration_high"] = True
                signals["task_state_running_timeout"] = True

        elif e.source == "cloudwatch_lambda_throttles":
            if p.get("lambda_throttled"):
                signals["aws_lambda_error_count_high"] = True  # throttles count as failures

        # ── CloudTrail ───────────────────────────────────────────────────────
        elif e.source == "cloudtrail_lambda_invoke":
            if p.get("cloudtrail_event_found"):
                signals["cloudtrail_event_found"] = True

        elif e.source == "cloudtrail_iam_changes":
            if p.get("iam_policy_changed"):
                signals["iam_policy_changed"] = True
                # IAM changes + task failure is a strong permission error signal
                if signals.get("task_state_failed"):
                    signals["task_logs_contain_permission_error"] = True

        elif e.source == "cloudtrail_config_changes":
            if p.get("config_changed"):
                signals["dag_schedule_changed"] = True

        # ── Redis ────────────────────────────────────────────────────────────
        elif e.source == "redis_health":
            if not p.get("redis_healthy"):
                signals["scheduler_state_unhealthy"] = True  # broker down = scheduler impact
            if p.get("celery_queue_saturated"):
                signals["pool_queued_slots_high"] = True
                signals["concurrent_tasks_high"] = True

        elif e.source == "redis_queue_depth":
            if p.get("queue_saturated"):
                signals["pool_queued_slots_high"] = True
                signals["queued_tasks_high"] = True

        # ── Postgres ─────────────────────────────────────────────────────────
        elif e.source == "postgres_connections":
            if p.get("connection_pool_high"):
                signals["db_connection_high"] = True
                signals["scheduler_db_unhealthy"] = True

        elif e.source == "postgres_slow_queries":
            if p.get("db_contention_detected"):
                signals["db_connection_high"] = True

        # ── Cost Explorer ────────────────────────────────────────────────────
        elif e.source == "cost_explorer_lambda":
            if p.get("cost_delta_high"):
                signals["cost_delta_high"] = True

        # ── S3 Metadata ──────────────────────────────────────────────────────
        elif e.source == "s3_metadata":
            if p.get("s3_prefix_empty"):
                signals["s3_prefix_empty"] = True

    return NormalizedEvidenceBundle(
        signals=signals,
        evidence_ids=evidence_ids,
        source_count=len(sources)
    )
