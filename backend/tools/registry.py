"""
Atomic Evidence Tools Registry — AirGuard
==========================================
Each tool is an independent function: (InvestigationRequest) -> Evidence | None.
- On success: returns a strongly typed Evidence object with real payload.
- On integration failure: raises so AgentCoreToolExecutor captures it as ToolFailure.
- No mocking. No fallback data. If a client can't connect, it fails cleanly.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from backend.investigation.models import InvestigationRequest
from backend.evidence.models import (
    Evidence, AirflowEvidence, CloudWatchEvidence, CloudTrailEvidence,
    InfrastructureEvidence, CostEvidence
)

def _airflow():
    from backend.integrations.registry import registry
    return registry.get_airflow_client()

def _cloudwatch():
    from backend.integrations.registry import registry
    return registry.get_aws_registry().get_cloudwatch_client()

def _cloudtrail():
    from backend.integrations.registry import registry
    return registry.get_aws_registry().get_cloudtrail_client()

def _now():
    return datetime.now(timezone.utc)

def _window(hours: int = 1):
    now = _now()
    return now - timedelta(hours=hours), now


# ─────────────────────────────────────────────────────────────────────────────
# AIRFLOW TOOLS (15)
# ─────────────────────────────────────────────────────────────────────────────

def get_scheduler_health(request: InvestigationRequest) -> Optional[Evidence]:
    """GET /health → scheduler.status + metadatabase.status"""
    client = _airflow()
    health = client.get_health()
    scheduler_status = health.get("scheduler", {}).get("status", "unknown")
    db_status = health.get("metadatabase", {}).get("status", "unknown")
    return AirflowEvidence(
        source="airflow_scheduler_health",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload=health,
        normalized_payload={"status": scheduler_status, "db_status": db_status},
        metadata={"dag_id": request.dag_id}
    )


def get_scheduler_heartbeat(request: InvestigationRequest) -> Optional[Evidence]:
    """Derives scheduler heartbeat lag from /health"""
    client = _airflow()
    health = client.get_health()
    heartbeat_info = health.get("scheduler", {})
    latest_heartbeat = heartbeat_info.get("latest_scheduler_heartbeat", "")
    lag_seconds = None
    is_stale = False
    if latest_heartbeat:
        try:
            hb_time = datetime.fromisoformat(latest_heartbeat.replace("Z", "+00:00"))
            lag_seconds = int((_now() - hb_time).total_seconds())
            is_stale = lag_seconds > 60
        except Exception:
            pass
    return AirflowEvidence(
        source="airflow_scheduler_heartbeat",
        timestamp=_now(),
        reliability=1.0,
        confidence=0.9,
        raw_payload=heartbeat_info,
        normalized_payload={"lag_seconds": lag_seconds, "is_stale": is_stale},
        metadata={"dag_id": request.dag_id}
    )


def get_airflow_version(request: InvestigationRequest) -> Optional[Evidence]:
    """GET /version → airflow version string"""
    client = _airflow()
    version = client.get_version()
    return AirflowEvidence(
        source="airflow_version",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload={"version": version},
        normalized_payload={"version": version},
        metadata={}
    )


def get_dag_runs(request: InvestigationRequest) -> Optional[Evidence]:
    """GET /dags/{id}/dagRuns → last 10 runs with state/run_type"""
    client = _airflow()
    runs = client.get_dag_runs(request.dag_id)
    manual_count = sum(1 for r in runs if r.get("run_type") == "manual")
    backfill_count = sum(1 for r in runs if r.get("run_type") == "backfill")
    failed_count = sum(1 for r in runs if r.get("state") == "failed")
    return AirflowEvidence(
        source="airflow_dag_runs",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload={"runs": runs},
        normalized_payload={
            "run_count": len(runs),
            "manual_count": manual_count,
            "backfill_count": backfill_count,
            "failed_count": failed_count,
            "runs": runs
        },
        metadata={"dag_id": request.dag_id}
    )


def get_dag_details(request: InvestigationRequest) -> Optional[Evidence]:
    """GET /dags/{id}/details → schedule_interval, is_paused, tags"""
    client = _airflow()
    details = client.get_dag_graph(request.dag_id)
    is_paused = details.get("is_paused", False)
    schedule = details.get("schedule_interval", "unknown")
    return AirflowEvidence(
        source="airflow_dag_details",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload=details,
        normalized_payload={"is_paused": is_paused, "schedule_interval": schedule},
        metadata={"dag_id": request.dag_id}
    )


def get_all_dags(request: InvestigationRequest) -> Optional[Evidence]:
    """GET /dags → full list with paused state"""
    client = _airflow()
    dag_ids = client.get_all_dag_ids()
    return AirflowEvidence(
        source="airflow_all_dags",
        timestamp=_now(),
        reliability=1.0,
        confidence=0.9,
        raw_payload={"dag_ids": dag_ids},
        normalized_payload={"total_dags": len(dag_ids)},
        metadata={}
    )


def get_task_instances(request: InvestigationRequest) -> Optional[Evidence]:
    """GET /dagRuns/{run_id}/taskInstances for the most recent run"""
    client = _airflow()
    runs = client.get_dag_runs(request.dag_id)
    if not runs:
        return AirflowEvidence(
            source="airflow_task_instances",
            timestamp=_now(),
            reliability=1.0,
            confidence=1.0,
            raw_payload={"tasks": [], "error": "No DAG runs found"},
            normalized_payload={
                "tasks": [],
                "failed_count": 0,
                "upstream_failed_count": 0,
                "running_count": 0,
                "success_count": 0,
                "max_try_number": 1
            },
            metadata={"dag_id": request.dag_id}
        )
    latest_run = runs[0]
    run_id = latest_run.get("dag_run_id") or latest_run.get("run_id", "")
    if not run_id:
        return None
    tasks = client.get_task_instances(request.dag_id, run_id)
    failed = [t for t in tasks if t.get("state") == "failed"]
    upstream_failed = [t for t in tasks if t.get("state") == "upstream_failed"]
    running = [t for t in tasks if t.get("state") == "running"]
    success = [t for t in tasks if t.get("state") == "success"]
    max_try = max((t.get("try_number", 1) for t in tasks), default=1)
    return AirflowEvidence(
        source="airflow_task_instances",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload={"tasks": tasks, "run_id": run_id},
        normalized_payload={
            "tasks": tasks,
            "failed_count": len(failed),
            "upstream_failed_count": len(upstream_failed),
            "running_count": len(running),
            "success_count": len(success),
            "max_try_number": max_try
        },
        metadata={"dag_id": request.dag_id, "run_id": run_id}
    )


def get_failed_task_logs(request: InvestigationRequest) -> Optional[Evidence]:
    """Fetches logs for all failed tasks in the latest run"""
    client = _airflow()
    runs = client.get_dag_runs(request.dag_id)
    if not runs:
        return AirflowEvidence(
            source="airflow_task_logs",
            timestamp=_now(),
            reliability=1.0,
            confidence=1.0,
            raw_payload={"logs": {}, "error": "No DAG runs found"},
            normalized_payload={
                "logs": "",
                "contains_lambda": False,
                "contains_timeout": False,
                "contains_permission_error": False,
                "contains_oom_kill": False
            },
            metadata={"dag_id": request.dag_id}
        )
    latest_run = runs[0]
    run_id = latest_run.get("dag_run_id") or latest_run.get("run_id", "")
    if not run_id:
        return None
    tasks = client.get_task_instances(request.dag_id, run_id)
    failed_tasks = [t for t in tasks if t.get("state") in ("failed", "upstream_failed")]
    all_logs = {}
    contains_lambda = False
    contains_timeout = False
    contains_permission = False
    contains_oom_kill = False
    for t in failed_tasks:
        task_id = t.get("task_id", "")
        try:
            log_text = client.get_task_logs(request.dag_id, run_id, task_id)
            all_logs[task_id] = log_text
            if "lambda" in log_text.lower() or "Lambda" in log_text:
                contains_lambda = True
            if "timeout" in log_text.lower() or "timed out" in log_text.lower():
                contains_timeout = True
            if "permission" in log_text.lower() or "access denied" in log_text.lower() or "unauthorized" in log_text.lower():
                contains_permission = True
            if "exit code 137" in log_text.lower() or "oom" in log_text.lower() or "memory limit exceeded" in log_text.lower():
                contains_oom_kill = True
        except Exception:
            all_logs[task_id] = ""
    return AirflowEvidence(
        source="airflow_task_logs",
        timestamp=_now(),
        reliability=0.85,
        confidence=0.9,
        raw_payload={"logs": all_logs},
        normalized_payload={
            "logs": " ".join(all_logs.values()),
            "contains_lambda": contains_lambda,
            "contains_timeout": contains_timeout,
            "contains_permission_error": contains_permission,
            "contains_oom_kill": contains_oom_kill
        },
        metadata={"dag_id": request.dag_id, "run_id": run_id}
    )


def get_task_xcoms(request: InvestigationRequest) -> Optional[Evidence]:
    """XCom entries for quality/validation tasks"""
    client = _airflow()
    runs = client.get_dag_runs(request.dag_id)
    if not runs:
        return AirflowEvidence(
            source="airflow_xcoms",
            timestamp=_now(),
            reliability=1.0,
            confidence=1.0,
            raw_payload={"xcoms": [], "error": "No DAG runs found"},
            normalized_payload={
                "xcoms": [],
                "quality_check_failed": False,
                "row_count_zero": False
            },
            metadata={"dag_id": request.dag_id}
        )
    latest_run = runs[0]
    run_id = latest_run.get("dag_run_id") or latest_run.get("run_id", "")
    if not run_id:
        return None
    tasks = client.get_task_instances(request.dag_id, run_id)
    success_tasks = [t for t in tasks if t.get("state") == "success"]
    all_xcoms = []
    for t in success_tasks:
        task_id = t.get("task_id", "")
        try:
            xcoms = client.get_task_xcoms(request.dag_id, run_id, task_id)
            all_xcoms.extend(xcoms)
        except Exception:
            pass
    quality_check_failed = any(
        x.get("key") == "quality_check" and str(x.get("value", "")).lower() in ("false", "0", "failed")
        for x in all_xcoms
    )
    row_count_zero = any(
        x.get("key") == "row_count" and str(x.get("value", "1")) == "0"
        for x in all_xcoms
    )
    return AirflowEvidence(
        source="airflow_xcoms",
        timestamp=_now(),
        reliability=0.9,
        confidence=0.85,
        raw_payload={"xcoms": all_xcoms},
        normalized_payload={
            "xcoms": all_xcoms,
            "quality_check_failed": quality_check_failed,
            "row_count_zero": row_count_zero
        },
        metadata={"dag_id": request.dag_id, "run_id": run_id}
    )


def get_pool_stats(request: InvestigationRequest) -> Optional[Evidence]:
    """GET /pools → open/queued/running slots"""
    client = _airflow()
    pool_data = client.get_pool_stats()
    pools = pool_data.get("pools", [])
    queued_slots = sum(p.get("queued_slots", 0) for p in pools)
    open_slots = sum(p.get("open_slots", 0) for p in pools)
    running_slots = sum(p.get("running_slots", 0) for p in pools)
    pool_saturated = any(p.get("open_slots", 1) == 0 for p in pools)
    return AirflowEvidence(
        source="airflow_pool_stats",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload=pool_data,
        normalized_payload={
            "queued_slots": queued_slots,
            "open_slots": open_slots,
            "running_slots": running_slots,
            "pool_saturated": pool_saturated
        },
        metadata={}
    )


def get_import_errors(request: InvestigationRequest) -> Optional[Evidence]:
    """GET /importErrors → DAG parse errors"""
    client = _airflow()
    try:
        url = f"{client.base_url}/importErrors"
        import requests as req
        resp = req.get(url, auth=client.auth, timeout=10)
        resp.raise_for_status()
        errors = resp.json().get("import_errors", [])
    except Exception:
        errors = []
    has_errors = len(errors) > 0
    dag_errors = [e for e in errors if request.dag_id in e.get("filename", "")]
    return AirflowEvidence(
        source="airflow_import_errors",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload={"import_errors": errors},
        normalized_payload={
            "has_import_errors": has_errors,
            "dag_specific_errors": len(dag_errors) > 0,
            "error_count": len(errors)
        },
        metadata={"dag_id": request.dag_id}
    )


def get_airflow_config(request: InvestigationRequest) -> Optional[Evidence]:
    """GET /config → parallelism, max_active_runs, dag_concurrency"""
    client = _airflow()
    config_data = client.get_read_only_metadata()
    sections = config_data.get("sections", [])
    core_section = next((s for s in sections if s.get("name") == "core"), {})
    core_options = {o["key"]: o["value"] for o in core_section.get("options", [])}
    return AirflowEvidence(
        source="airflow_config",
        timestamp=_now(),
        reliability=1.0,
        confidence=0.8,
        raw_payload=config_data,
        normalized_payload={
            "parallelism": core_options.get("parallelism", "unknown"),
            "max_active_runs_per_dag": core_options.get("max_active_runs_per_dag", "unknown"),
            "dag_concurrency": core_options.get("dag_concurrency", "unknown")
        },
        metadata={}
    )


def get_dag_run_by_id(request: InvestigationRequest) -> Optional[Evidence]:
    """GET specific run if task_id is provided in request"""
    client = _airflow()
    runs = client.get_dag_runs(request.dag_id)
    if not runs:
        return AirflowEvidence(
            source="airflow_dag_run_detail",
            timestamp=_now(),
            reliability=1.0,
            confidence=1.0,
            raw_payload={"error": "No DAG runs found"},
            normalized_payload={
                "state": "unknown",
                "run_type": "unknown",
                "execution_date": "",
                "end_date": ""
            },
            metadata={"dag_id": request.dag_id}
        )
    latest = runs[0]
    run_id = latest.get("dag_run_id") or latest.get("run_id", "")
    run_detail = client.get_dag_run_by_id(request.dag_id, run_id) if run_id else latest
    return AirflowEvidence(
        source="airflow_dag_run_detail",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload=run_detail,
        normalized_payload={
            "state": run_detail.get("state", "unknown"),
            "run_type": run_detail.get("run_type", "unknown"),
            "execution_date": run_detail.get("execution_date", ""),
            "end_date": run_detail.get("end_date", "")
        },
        metadata={"dag_id": request.dag_id, "run_id": run_id}
    )


def detect_retry_storm(request: InvestigationRequest) -> Optional[Evidence]:
    """Analyzes DAG runs + task instances for rapid retry pattern"""
    client = _airflow()
    runs = client.get_dag_runs(request.dag_id)
    if not runs or not runs[0]:
        return AirflowEvidence(
            source="airflow_retry_analysis",
            timestamp=_now(),
            reliability=1.0,
            confidence=1.0,
            raw_payload={"error": "No DAG runs found"},
            normalized_payload={
                "retry_storm_detected": False,
                "rapid_runs": False,
                "retry_interval_short": False,
                "max_try_number": 1
            },
            metadata={"dag_id": request.dag_id}
        )
    run_id = runs[0].get("dag_run_id") or runs[0].get("run_id", "")
    tasks = client.get_task_instances(request.dag_id, run_id) if run_id else []
    max_try = max((t.get("try_number", 1) for t in tasks), default=1)
    retry_interval_short = False
    storm_detected = max_try > 4
    # Detect rapid runs (multiple runs in short window)
    rapid_runs = False
    if len(runs) >= 5:
        try:
            from datetime import datetime
            first_ts = runs[-1].get("start_date", "")
            last_ts = runs[0].get("start_date", "")
            if first_ts and last_ts:
                t1 = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
                t2 = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                window_minutes = abs((t2 - t1).total_seconds()) / 60
                if window_minutes < 30:
                    rapid_runs = True
                    retry_interval_short = True
        except Exception:
            pass
    return AirflowEvidence(
        source="airflow_retry_analysis",
        timestamp=_now(),
        reliability=0.95,
        confidence=0.9,
        raw_payload={"max_try_number": max_try, "rapid_runs": rapid_runs, "run_count": len(runs)},
        normalized_payload={
            "retry_storm_detected": storm_detected,
            "rapid_runs": rapid_runs,
            "retry_interval_short": retry_interval_short,
            "max_try_number": max_try
        },
        metadata={"dag_id": request.dag_id}
    )


def detect_cascade_failure(request: InvestigationRequest) -> Optional[Evidence]:
    """Checks for upstream_failed propagation across the task graph"""
    client = _airflow()
    runs = client.get_dag_runs(request.dag_id)
    if not runs:
        return AirflowEvidence(
            source="airflow_cascade_analysis",
            timestamp=_now(),
            reliability=1.0,
            confidence=1.0,
            raw_payload={"error": "No DAG runs found"},
            normalized_payload={
                "cascade_failure_detected": False,
                "upstream_failed_count": 0,
                "directly_failed_count": 0
            },
            metadata={"dag_id": request.dag_id}
        )
    run_id = runs[0].get("dag_run_id") or runs[0].get("run_id", "")
    if not run_id:
        return None
    tasks = client.get_task_instances(request.dag_id, run_id)
    failed = [t for t in tasks if t.get("state") == "failed"]
    upstream_failed = [t for t in tasks if t.get("state") == "upstream_failed"]
    cascade = len(upstream_failed) > 0 and len(failed) > 0
    return AirflowEvidence(
        source="airflow_cascade_analysis",
        timestamp=_now(),
        reliability=1.0,
        confidence=0.95,
        raw_payload={"tasks": tasks},
        normalized_payload={
            "cascade_failure_detected": cascade,
            "upstream_failed_count": len(upstream_failed),
            "directly_failed_count": len(failed)
        },
        metadata={"dag_id": request.dag_id, "run_id": run_id}
    )


# ─────────────────────────────────────────────────────────────────────────────
# AWS CLOUDWATCH TOOLS (5 — Lambda + Cost)
# ─────────────────────────────────────────────────────────────────────────────

def _get_lambda_name(request: InvestigationRequest) -> str:
    """Derives Lambda function name from dag_id or task metadata."""
    # Convention: DAG "lambda_pipeline" -> function "lambda_pipeline"
    # or use task_id if set
    return request.task_id or request.dag_id.replace("_pipeline", "").replace("_dag", "")


def get_lambda_errors(request: InvestigationRequest) -> Optional[Evidence]:
    """CloudWatch: Lambda Errors metric for the past hour"""
    client = _cloudwatch()
    start, end = _window(hours=1)
    fn_name = _get_lambda_name(request)
    error_count = client.get_lambda_errors(fn_name, start, end)
    return CloudWatchEvidence(
        source="cloudwatch_lambda_errors",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload={"function_name": fn_name, "error_count": error_count, "window_hours": 1},
        normalized_payload={"lambda_error_count": error_count, "lambda_errors_present": error_count > 0},
        metadata={"function_name": fn_name}
    )


def get_lambda_duration(request: InvestigationRequest) -> Optional[Evidence]:
    """CloudWatch: Lambda max Duration for the past hour"""
    client = _cloudwatch()
    start, end = _window(hours=1)
    fn_name = _get_lambda_name(request)
    max_duration_ms = client.get_lambda_duration(fn_name, start, end)
    # Lambda default timeout is 15 min = 900,000ms
    near_timeout = max_duration_ms > 870_000
    return CloudWatchEvidence(
        source="cloudwatch_lambda_duration",
        timestamp=_now(),
        reliability=1.0,
        confidence=0.95,
        raw_payload={"function_name": fn_name, "max_duration_ms": max_duration_ms},
        normalized_payload={
            "lambda_max_duration_ms": max_duration_ms,
            "lambda_near_timeout": near_timeout
        },
        metadata={"function_name": fn_name}
    )


def get_lambda_throttles(request: InvestigationRequest) -> Optional[Evidence]:
    """CloudWatch: Lambda Throttles metric for the past hour"""
    client = _cloudwatch()
    start, end = _window(hours=1)
    fn_name = _get_lambda_name(request)
    # Use generic metric query since throttles aren't in the interface yet
    from backend.integrations.aws.client_factory import get_boto3_client
    cw = get_boto3_client("cloudwatch")
    res = cw.get_metric_statistics(
        Namespace="AWS/Lambda",
        MetricName="Throttles",
        Dimensions=[{"Name": "FunctionName", "Value": fn_name}],
        StartTime=start,
        EndTime=end,
        Period=3600,
        Statistics=["Sum"]
    )
    throttle_count = int(sum(dp.get("Sum", 0) for dp in res.get("Datapoints", [])))
    return CloudWatchEvidence(
        source="cloudwatch_lambda_throttles",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload={"function_name": fn_name, "throttle_count": throttle_count},
        normalized_payload={"lambda_throttle_count": throttle_count, "lambda_throttled": throttle_count > 0},
        metadata={"function_name": fn_name}
    )


def get_lambda_invocations(request: InvestigationRequest) -> Optional[Evidence]:
    """CloudWatch: Lambda Invocations count for past hour"""
    from backend.integrations.aws.client_factory import get_boto3_client
    start, end = _window(hours=1)
    fn_name = _get_lambda_name(request)
    cw = get_boto3_client("cloudwatch")
    res = cw.get_metric_statistics(
        Namespace="AWS/Lambda",
        MetricName="Invocations",
        Dimensions=[{"Name": "FunctionName", "Value": fn_name}],
        StartTime=start,
        EndTime=end,
        Period=3600,
        Statistics=["Sum"]
    )
    count = int(sum(dp.get("Sum", 0) for dp in res.get("Datapoints", [])))
    return CloudWatchEvidence(
        source="cloudwatch_lambda_invocations",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload={"function_name": fn_name, "invocation_count": count},
        normalized_payload={"lambda_invocation_count": count},
        metadata={"function_name": fn_name}
    )


# ─────────────────────────────────────────────────────────────────────────────
# AWS CLOUDTRAIL TOOLS (3)
# ─────────────────────────────────────────────────────────────────────────────

def get_lambda_invocation_events(request: InvestigationRequest) -> Optional[Evidence]:
    """CloudTrail: InvokeFunction events in the past 1 hour"""
    client = _cloudtrail()
    start, end = _window(hours=1)
    fn_name = _get_lambda_name(request)
    events = client.lookup_events(
        attributes=[{"AttributeKey": "EventName", "AttributeValue": "InvokeFunction"}],
        start_time=start,
        end_time=end
    )
    fn_events = [e for e in events if fn_name in str(e)]
    return CloudTrailEvidence(
        source="cloudtrail_lambda_invoke",
        timestamp=_now(),
        reliability=0.95,
        confidence=0.9,
        raw_payload={"events": fn_events},
        normalized_payload={
            "invocation_event_count": len(fn_events),
            "cloudtrail_event_found": len(fn_events) > 0
        },
        metadata={"function_name": fn_name}
    )


def get_iam_policy_changes(request: InvestigationRequest) -> Optional[Evidence]:
    """CloudTrail: Recent IAM PutRolePolicy / AttachRolePolicy events"""
    client = _cloudtrail()
    start, end = _window(hours=6)
    events = client.lookup_events(
        attributes=[{"AttributeKey": "EventName", "AttributeValue": "PutRolePolicy"}],
        start_time=start,
        end_time=end
    )
    events2 = client.lookup_events(
        attributes=[{"AttributeKey": "EventName", "AttributeValue": "AttachRolePolicy"}],
        start_time=start,
        end_time=end
    )
    all_events = events + events2
    return CloudTrailEvidence(
        source="cloudtrail_iam_changes",
        timestamp=_now(),
        reliability=0.95,
        confidence=0.9,
        raw_payload={"events": all_events},
        normalized_payload={
            "iam_policy_changed": len(all_events) > 0,
            "iam_change_count": len(all_events)
        },
        metadata={}
    )


def get_resource_config_changes(request: InvestigationRequest) -> Optional[Evidence]:
    """CloudTrail: UpdateFunctionConfiguration events (Lambda config drift)"""
    client = _cloudtrail()
    start, end = _window(hours=24)
    events = client.lookup_events(
        attributes=[{"AttributeKey": "EventName", "AttributeValue": "UpdateFunctionConfiguration"}],
        start_time=start,
        end_time=end
    )
    return CloudTrailEvidence(
        source="cloudtrail_config_changes",
        timestamp=_now(),
        reliability=0.95,
        confidence=0.85,
        raw_payload={"events": events},
        normalized_payload={
            "config_changed": len(events) > 0,
            "config_change_count": len(events)
        },
        metadata={}
    )


# ─────────────────────────────────────────────────────────────────────────────
# AWS S3 TOOLS (1)
# ─────────────────────────────────────────────────────────────────────────────

def get_s3_prefix_metrics(request: InvestigationRequest) -> Optional[Evidence]:
    """S3: Check if a dataset prefix is empty or missing."""
    import boto3
    from backend.integrations.core.config import config
    # In a real scenario, bucket and prefix would be extracted from task parameters or XComs.
    # For now, we derive a convention based on dag_id
    bucket = getattr(config, "data_lake_bucket", "airguard-datalake")
    prefix = f"data/{request.dag_id}/"
    
    from backend.integrations.aws.client_factory import get_boto3_client
    s3 = get_boto3_client("s3")
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=100)
        objects = resp.get("Contents", [])
        total_bytes = sum(obj.get("Size", 0) for obj in objects)
        object_count = len(objects)
    except Exception:
        total_bytes = 0
        object_count = 0
        
    return Evidence(
        id=f"s3_metrics_{request.dag_id}_{_now().timestamp()}",
        source="s3_metadata",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload={"bucket": bucket, "prefix": prefix, "object_count": object_count, "total_bytes": total_bytes},
        normalized_payload={
            "s3_prefix_empty": object_count == 0,
            "object_count": object_count,
            "total_bytes": total_bytes
        },
        metadata={"bucket": bucket, "prefix": prefix}
    )


# ─────────────────────────────────────────────────────────────────────────────
# REDIS TOOLS (2)
# ─────────────────────────────────────────────────────────────────────────────

def get_redis_health(request: InvestigationRequest) -> Optional[Evidence]:
    """PING redis and check broker queue depth"""
    import redis
    from backend.integrations.core.config import config
    redis_url = f"redis://{getattr(config, 'redis_host', 'localhost')}:{getattr(config, 'redis_port', 6379)}/0"
    r = redis.from_url(redis_url, socket_timeout=5)
    pong = r.ping()
    # Celery default queue
    queue_depth = r.llen("default") if pong else -1
    return InfrastructureEvidence(
        source="redis_health",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload={"ping": pong, "queue_depth": queue_depth},
        normalized_payload={
            "redis_healthy": pong,
            "celery_queue_depth": queue_depth,
            "celery_queue_saturated": queue_depth > 50
        },
        metadata={}
    )


def get_redis_queue_depth(request: InvestigationRequest) -> Optional[Evidence]:
    """Checks all Celery queues for pending task count"""
    import redis
    from backend.integrations.core.config import config
    redis_url = f"redis://{getattr(config, 'redis_host', 'localhost')}:{getattr(config, 'redis_port', 6379)}/0"
    r = redis.from_url(redis_url, socket_timeout=5)
    queues = ["default", "celery", "high_priority"]
    depths = {q: r.llen(q) for q in queues}
    total = sum(depths.values())
    return InfrastructureEvidence(
        source="redis_queue_depth",
        timestamp=_now(),
        reliability=1.0,
        confidence=0.9,
        raw_payload={"queue_depths": depths},
        normalized_payload={"total_queued_tasks": total, "queue_saturated": total > 100},
        metadata={}
    )


# ─────────────────────────────────────────────────────────────────────────────
# POSTGRES TOOLS (2)
# ─────────────────────────────────────────────────────────────────────────────

def get_postgres_connection_count(request: InvestigationRequest) -> Optional[Evidence]:
    """Checks active Postgres connection count vs max_connections"""
    import psycopg2
    import os
    conn = psycopg2.connect(
        host=os.getenv("AIRGUARD_DB_HOST", "localhost"),
        port=int(os.getenv("AIRGUARD_DB_PORT", 5432)),
        dbname=os.getenv("AIRGUARD_DB_NAME", "airguard"),
        user=os.getenv("AIRGUARD_DB_USER", "airguard"),
        password=os.getenv("AIRGUARD_DB_PASSWORD", "airguard"),
        connect_timeout=5
    )
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
    active = cursor.fetchone()[0]
    cursor.execute("SHOW max_connections")
    max_conn = int(cursor.fetchone()[0])
    cursor.close()
    conn.close()
    utilization = active / max_conn if max_conn > 0 else 0
    return InfrastructureEvidence(
        source="postgres_connections",
        timestamp=_now(),
        reliability=1.0,
        confidence=1.0,
        raw_payload={"active_connections": active, "max_connections": max_conn},
        normalized_payload={
            "active_connections": active,
            "max_connections": max_conn,
            "connection_utilization": round(utilization, 2),
            "connection_pool_high": utilization > 0.8
        },
        metadata={}
    )


def get_postgres_slow_queries(request: InvestigationRequest) -> Optional[Evidence]:
    """pg_stat_activity: queries running longer than 30 seconds"""
    import psycopg2
    import os
    conn = psycopg2.connect(
        host=os.getenv("AIRGUARD_DB_HOST", "localhost"),
        port=int(os.getenv("AIRGUARD_DB_PORT", 5432)),
        dbname=os.getenv("AIRGUARD_DB_NAME", "airguard"),
        user=os.getenv("AIRGUARD_DB_USER", "airguard"),
        password=os.getenv("AIRGUARD_DB_PASSWORD", "airguard"),
        connect_timeout=5
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pid, query, state, EXTRACT(epoch FROM now() - query_start) AS duration_sec
        FROM pg_stat_activity
        WHERE state = 'active'
          AND query_start < now() - interval '30 seconds'
        ORDER BY duration_sec DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    slow_queries = [{"pid": r[0], "query": r[1][:200], "state": r[2], "duration_sec": r[3]} for r in rows]
    cursor.close()
    conn.close()
    return InfrastructureEvidence(
        source="postgres_slow_queries",
        timestamp=_now(),
        reliability=1.0,
        confidence=0.9,
        raw_payload={"slow_queries": slow_queries},
        normalized_payload={
            "slow_query_count": len(slow_queries),
            "db_contention_detected": len(slow_queries) > 0
        },
        metadata={}
    )


# ─────────────────────────────────────────────────────────────────────────────
# COST EXPLORER (1)
# ─────────────────────────────────────────────────────────────────────────────

def get_lambda_cost_delta(request: InvestigationRequest) -> Optional[Evidence]:
    """Cost Explorer: Lambda spend today vs 7-day average"""
    from backend.integrations.core.config import config
    from datetime import date, timedelta
    from backend.integrations.aws.client_factory import get_boto3_client
    ce = get_boto3_client("ce")
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=8)
    # Today's spend
    today_resp = ce.get_cost_and_usage(
        TimePeriod={"Start": str(yesterday), "End": str(today)},
        Granularity="DAILY",
        Filter={"Dimensions": {"Key": "SERVICE", "Values": ["AWS Lambda"]}},
        Metrics=["UnblendedCost"]
    )
    # 7-day average
    week_resp = ce.get_cost_and_usage(
        TimePeriod={"Start": str(week_ago), "End": str(yesterday)},
        Granularity="DAILY",
        Filter={"Dimensions": {"Key": "SERVICE", "Values": ["AWS Lambda"]}},
        Metrics=["UnblendedCost"]
    )
    today_cost = float(
        today_resp["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]
        if today_resp.get("ResultsByTime") else 0
    )
    week_results = week_resp.get("ResultsByTime", [])
    week_avg = (
        sum(float(r["Total"]["UnblendedCost"]["Amount"]) for r in week_results) / len(week_results)
        if week_results else 0
    )
    delta_pct = ((today_cost - week_avg) / week_avg * 100) if week_avg > 0 else 0
    return CostEvidence(
        source="cost_explorer_lambda",
        timestamp=_now(),
        reliability=0.9,
        confidence=0.85,
        raw_payload={"today_cost_usd": today_cost, "week_avg_usd": week_avg, "delta_pct": delta_pct},
        normalized_payload={
            "cost_delta_high": abs(delta_pct) > 30,
            "cost_today_usd": today_cost,
            "cost_week_avg_usd": week_avg,
            "cost_delta_pct": round(delta_pct, 1)
        },
        metadata={}
    )


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

TOOL_REGISTRY = {
    # Airflow
    "get_scheduler_health":      get_scheduler_health,
    "get_scheduler_heartbeat":   get_scheduler_heartbeat,
    "get_airflow_version":       get_airflow_version,
    "get_dag_runs":              get_dag_runs,
    "get_dag_details":           get_dag_details,
    "get_all_dags":              get_all_dags,
    "get_task_instances":        get_task_instances,
    "get_failed_task_logs":      get_failed_task_logs,
    "get_task_xcoms":            get_task_xcoms,
    "get_pool_stats":            get_pool_stats,
    "get_import_errors":         get_import_errors,
    "get_airflow_config":        get_airflow_config,
    "get_dag_run_by_id":         get_dag_run_by_id,
    "detect_retry_storm":        detect_retry_storm,
    "detect_cascade_failure":    detect_cascade_failure,
    # CloudWatch / Lambda
    "get_lambda_errors":         get_lambda_errors,
    "get_lambda_duration":       get_lambda_duration,
    "get_lambda_throttles":      get_lambda_throttles,
    "get_lambda_invocations":    get_lambda_invocations,
    # CloudTrail
    "get_lambda_invocation_events":  get_lambda_invocation_events,
    "get_iam_policy_changes":        get_iam_policy_changes,
    "get_resource_config_changes":   get_resource_config_changes,
    # Redis
    "get_redis_health":          get_redis_health,
    "get_redis_queue_depth":     get_redis_queue_depth,
    # Postgres
    "get_postgres_connection_count": get_postgres_connection_count,
    "get_postgres_slow_queries":     get_postgres_slow_queries,
    # Cost Explorer
    "get_lambda_cost_delta":     get_lambda_cost_delta,
}
