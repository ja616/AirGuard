from typing import List
from backend.investigation.models import ClassifiedIncident, RecommendedAction

from typing import List
from backend.investigation.models import ClassifiedIncident, RecommendedAction, NormalizedEvidenceBundle

def run(classified: ClassifiedIncident, bundle: NormalizedEvidenceBundle) -> List[RecommendedAction]:
    actions = []
    signals = bundle.signals
    
    # Deterministic rule engine for recommendations based on active signals
    if signals.get("task_oom_killed"):
        actions.append(RecommendedAction(action="Increase worker memory limits or optimize task memory footprint."))
        
    if signals.get("scheduler_state_unhealthy"):
        actions.append(RecommendedAction(action="Restart the Airflow scheduler and verify metadata database connectivity."))
        
    if signals.get("aws_lambda_error_count_high"):
        actions.append(RecommendedAction(action="Check AWS CloudWatch logs for the specific Lambda function errors (timeout, code exception, etc)."))
        
    if signals.get("iam_policy_changed") and signals.get("task_state_failed"):
        actions.append(RecommendedAction(action="Review and potentially revert recent IAM policy changes in AWS CloudTrail."))
        
    if signals.get("db_connection_high"):
        actions.append(RecommendedAction(action="Increase Postgres max_connections or implement PgBouncer for connection pooling."))
        
    if signals.get("concurrent_tasks_high") and signals.get("pool_queued_slots_high"):
        actions.append(RecommendedAction(action="Increase Airflow pool size or scale out worker nodes to handle concurrency."))
        
    if signals.get("cost_delta_high"):
        actions.append(RecommendedAction(action="Review AWS Cost Explorer immediately to identify the specific service driving the spike."))
        
    if signals.get("task_retry_count_high") and signals.get("retry_interval_short"):
        actions.append(RecommendedAction(action="Implement exponential backoff for task retries to prevent API/resource hammering."))

    if signals.get("upstream_task_failed"):
        actions.append(RecommendedAction(action="Investigate and resolve the upstream dependency failure first."))
        
    if signals.get("xcom_quality_check_failed"):
        actions.append(RecommendedAction(action="Review upstream data source for missing or malformed records triggering XCom assertions."))
            
    # Fallback if no specific signal rules matched
    if not actions:
        actions.append(RecommendedAction(action="Review detailed task logs for unhandled exceptions."))
        
    return actions
