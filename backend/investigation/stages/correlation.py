from typing import List
from backend.investigation.models import EvidenceGraph, CorrelatedFinding, NormalizedEvidenceBundle

def run(graph: EvidenceGraph, bundle: NormalizedEvidenceBundle) -> List[CorrelatedFinding]:
    findings = []
    signals = bundle.signals
    
    if signals.get("task_retry_count_high") and signals.get("retry_interval_short"):
        findings.append(CorrelatedFinding(
            finding="Rapid retry pattern detected without backoff", 
            related_evidence=[n.id for n in graph.nodes],
            source="correlation_engine",
            severity="high",
            relevance_score=0.9
        ))
        
    if signals.get("upstream_task_failed") and signals.get("downstream_state_upstream_failed"):
        findings.append(CorrelatedFinding(
            finding="Cascade failure propagated from upstream dependency", 
            related_evidence=[n.id for n in graph.nodes],
            source="correlation_engine",
            severity="high",
            relevance_score=0.95
        ))
        
    if signals.get("task_duration_high"):
        findings.append(CorrelatedFinding(
            finding="Execution timeout anomaly detected", 
            related_evidence=[n.id for n in graph.nodes],
            source="correlation_engine",
            severity="medium",
            relevance_score=0.8
        ))
        
    if signals.get("aws_lambda_error_count_high"):
        findings.append(CorrelatedFinding(
            finding="AWS Lambda invocation failures strongly correlated with task failure", 
            related_evidence=[n.id for n in graph.nodes],
            source="aws_cloudwatch",
            severity="high",
            relevance_score=0.95
        ))
        
    if signals.get("scheduler_state_unhealthy"):
        findings.append(CorrelatedFinding(
            finding="Scheduler health degraded or offline", 
            related_evidence=[n.id for n in graph.nodes],
            source="airflow_health",
            severity="critical",
            relevance_score=1.0
        ))
        
    if signals.get("dag_schedule_changed"):
        findings.append(CorrelatedFinding(
            finding="Recent modification to DAG schedule detected", 
            related_evidence=[n.id for n in graph.nodes],
            source="metadata_audit",
            severity="medium",
            relevance_score=0.75
        ))
        
    if signals.get("manual_trigger_count_high"):
        findings.append(CorrelatedFinding(
            finding="High volume of manual DAG triggers in short window", 
            related_evidence=[n.id for n in graph.nodes],
            source="execution_history",
            severity="low",
            relevance_score=0.6
        ))
        
    if signals.get("concurrent_tasks_high") and signals.get("pool_queued_slots_high"):
        findings.append(CorrelatedFinding(
            finding="Task queueing due to Airflow pool starvation", 
            related_evidence=[n.id for n in graph.nodes],
            source="pool_metrics",
            severity="medium",
            relevance_score=0.85
        ))
        
    if signals.get("xcom_quality_check_failed"):
        findings.append(CorrelatedFinding(
            finding="Data quality XCom assertions failed despite task success", 
            related_evidence=[n.id for n in graph.nodes],
            source="xcom_telemetry",
            severity="high",
            relevance_score=0.9
        ))
        
    if signals.get("cost_delta_high"):
        findings.append(CorrelatedFinding(
            finding="Significant cost anomaly detected in external compute", 
            related_evidence=[n.id for n in graph.nodes],
            source="cost_explorer",
            severity="medium",
            relevance_score=0.8
        ))
        
    if signals.get("concurrent_tasks_maxed"):
        findings.append(CorrelatedFinding(
            finding="Explosive parallelism exceeding cluster capacity", 
            related_evidence=[n.id for n in graph.nodes],
            source="task_concurrency",
            severity="high",
            relevance_score=0.95
        ))

    if signals.get("iam_policy_changed") and signals.get("task_state_failed"):
        findings.append(CorrelatedFinding(
            finding="IAM policy mutation detected within 6h of task failure — execution permissions may have been revoked",
            related_evidence=[n.id for n in graph.nodes],
            source="cloudtrail_iam_changes",
            severity="high",
            relevance_score=0.92
        ))

    if signals.get("task_logs_contain_permission_error"):
        findings.append(CorrelatedFinding(
            finding="Task logs contain explicit permission or access denied errors",
            related_evidence=[n.id for n in graph.nodes],
            source="airflow_task_logs",
            severity="high",
            relevance_score=0.93
        ))

    if signals.get("db_connection_high"):
        findings.append(CorrelatedFinding(
            finding="Postgres connection pool near saturation — tasks may be unable to acquire database connections",
            related_evidence=[n.id for n in graph.nodes],
            source="postgres_connections",
            severity="medium",
            relevance_score=0.82
        ))

    if signals.get("cost_delta_high") and signals.get("aws_lambda_error_count_high"):
        findings.append(CorrelatedFinding(
            finding="Lambda error spike correlates with elevated spend — consider throttle limits or runaway invocations",
            related_evidence=[n.id for n in graph.nodes],
            source="cost_explorer_lambda",
            severity="medium",
            relevance_score=0.80
        ))

    if signals.get("cost_delta_high") and (signals.get("backfill_run_count_high") or signals.get("task_retry_count_high") or signals.get("rapid_runs")):
        findings.append(CorrelatedFinding(
            finding="Cost anomaly strongly correlated with excessive backfill runs or retry storms",
            related_evidence=[n.id for n in graph.nodes],
            source="cost_explorer",
            severity="high",
            relevance_score=0.95
        ))

    if not findings:
        findings.append(CorrelatedFinding(
            finding="Isolated task failure with no cascading correlation", 
            related_evidence=[n.id for n in graph.nodes],
            source="correlation_engine",
            severity="low",
            relevance_score=0.4
        ))
        
    return findings
