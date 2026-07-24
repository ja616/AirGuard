from typing import List
from backend.investigation.models import EvidenceGraph, CorrelatedFinding, NormalizedEvidenceBundle

def run(graph: EvidenceGraph, bundle: NormalizedEvidenceBundle) -> List[CorrelatedFinding]:
    findings = []
    signals = bundle.signals
    
    # 1. Retry Storms — signal from normalization: task_retry_count_high (set when max_try > 4)
    if signals.get("task_retry_count_high"):
        findings.append(CorrelatedFinding(
            finding="Rapid retry pattern detected without backoff", 
            related_evidence=[n.id for n in graph.nodes],
            source="correlation_engine",
            severity="high",
            relevance_score=0.9
        ))
        
    # 2. Timeout Anomaly — signal from normalization: task_state_running_timeout
    if signals.get("task_state_running_timeout"):
        findings.append(CorrelatedFinding(
            finding="Execution timeout anomaly detected", 
            related_evidence=[n.id for n in graph.nodes],
            source="correlation_engine",
            severity="medium",
            relevance_score=0.8
        ))

    # 3. Retry Storm + Timeout Anomaly
    if signals.get("task_state_running_timeout") and (signals.get("task_retry_count_high") or signals.get("task_state_failed")):
        findings.append(CorrelatedFinding(
            finding="Rapid Retry Storm + Timeout Anomaly", 
            related_evidence=[n.id for n in graph.nodes],
            source="correlation_engine",
            severity="critical",
            relevance_score=1.0
        ))

    # 3a. SageMaker Timeout Loop — specific sub-pattern of retry storm
    if signals.get("sagemaker_timeout_detected"):
        findings.append(CorrelatedFinding(
            finding="SageMaker training job timed out and left an orphaned job running in AWS while Airflow retried — classic Timeout Loop pattern",
            related_evidence=[n.id for n in graph.nodes],
            source="airflow_task_logs",
            severity="critical",
            relevance_score=1.0
        ))

    # 3b. SageMaker job involved with retries
    if signals.get("sagemaker_job_involved") and signals.get("task_retry_count_high"):
        findings.append(CorrelatedFinding(
            finding="SageMaker training job failed across multiple retries — each retry likely spawned a new orphaned training job in AWS",
            related_evidence=[n.id for n in graph.nodes],
            source="airflow_task_logs",
            severity="high",
            relevance_score=0.95
        ))
        
    # 4. Cascade Failure
    if signals.get("upstream_task_failed") and signals.get("downstream_state_upstream_failed"):
        findings.append(CorrelatedFinding(
            finding="Cascade failure propagated from upstream dependency", 
            related_evidence=[n.id for n in graph.nodes],
            source="correlation_engine",
            severity="high",
            relevance_score=0.95
        ))
        
    # 5. AWS Lambda Errors
    if signals.get("aws_lambda_error_count_high") or signals.get("contains_lambda"):
        findings.append(CorrelatedFinding(
            finding="AWS Lambda invocation failures strongly correlated with task failure", 
            related_evidence=[n.id for n in graph.nodes],
            source="aws_cloudwatch",
            severity="high",
            relevance_score=0.95
        ))
        
    # 6. Airflow Health
    if signals.get("scheduler_state_unhealthy") or signals.get("is_stale"):
        findings.append(CorrelatedFinding(
            finding="Scheduler health degraded or offline", 
            related_evidence=[n.id for n in graph.nodes],
            source="airflow_health",
            severity="critical",
            relevance_score=1.0
        ))
        
    # 7. Manual Triggers — signal from normalization: manual_trigger_count_high
    if signals.get("manual_trigger_count_high"):
        findings.append(CorrelatedFinding(
            finding="High volume of manual DAG triggers in short window", 
            related_evidence=[n.id for n in graph.nodes],
            source="execution_history",
            severity="low",
            relevance_score=0.6
        ))
        
    # 8. Queueing / Parallelism
    if signals.get("concurrent_tasks_high") or signals.get("pool_queued_slots_high"):
        findings.append(CorrelatedFinding(
            finding="Task queueing due to Airflow pool starvation", 
            related_evidence=[n.id for n in graph.nodes],
            source="pool_metrics",
            severity="medium",
            relevance_score=0.85
        ))
        
    # 9. Cost Spikes
    if signals.get("cost_delta_high"):
        findings.append(CorrelatedFinding(
            finding="Significant cost anomaly detected in external compute", 
            related_evidence=[n.id for n in graph.nodes],
            source="cost_explorer",
            severity="medium",
            relevance_score=0.8
        ))
        
    # 10. DEMO: The Phantom Retraining Storm (Cost Anomaly + Backfills)
    if signals.get("cost_delta_high") and (signals.get("backfill_count", 0) >= 5 or signals.get("rapid_runs") or signals.get("run_count", 0) > 20):
        findings.append(CorrelatedFinding(
            finding="Cost anomaly strongly correlated with excessive backfill runs or retry storms",
            related_evidence=[n.id for n in graph.nodes],
            source="cost_explorer",
            severity="high",
            relevance_score=0.95
        ))

    # 11. IAM / Permissions
    if signals.get("iam_policy_changed") or signals.get("contains_permission_error"):
        findings.append(CorrelatedFinding(
            finding="Task logs contain explicit permission or access denied errors",
            related_evidence=[n.id for n in graph.nodes],
            source="airflow_task_logs",
            severity="high",
            relevance_score=0.93
        ))

    # 12. Postgres
    if signals.get("connection_pool_high") or signals.get("db_contention_detected"):
        findings.append(CorrelatedFinding(
            finding="Postgres connection pool near saturation — tasks may be unable to acquire database connections",
            related_evidence=[n.id for n in graph.nodes],
            source="postgres_connections",
            severity="medium",
            relevance_score=0.82
        ))

    # Fallback
    if not findings:
        findings.append(CorrelatedFinding(
            finding="Isolated task failure with no cascading correlation", 
            related_evidence=[n.id for n in graph.nodes],
            source="correlation_engine",
            severity="low",
            relevance_score=0.4
        ))
        
    return findings
