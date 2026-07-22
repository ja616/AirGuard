"""
InvestigationPlanner — Context-Aware Capability Ranking

Architecture:
    IncidentContext
        → CapabilityScorer (scores each capability independently)
        → SeverityBudget (severity → top-N)
        → Ranked capability list
        → Tool resolution
        → InvestigationPlan

Key improvements over the previous profile-selection model:
  1. No "winner takes all" — all capabilities are scored independently.
  2. No unbounded merging — severity strictly caps how many capabilities
     are included (top-N), so the LLM never receives every available tool.
  3. Severity controls investigation budget, NOT domain selection.
  4. InvestigationGoal provides deterministic boosts for specific goals.
  5. SchedulerHealth is NOT activated by severity — only by orchestrator signals.
"""
from __future__ import annotations
from typing import List, Dict, Tuple
from backend.investigation.models import InvestigationRequest, IncidentContext, IncidentSeverity, InvestigationGoal
from backend.agent.planner.investigation_plan import InvestigationPlan, EvidenceCapability
from backend.skills.base import BaseSkill
from backend.skills.investigate_retry_storm import InvestigateRetryStormSkill


# ─────────────────────────────────────────────────────────────────────────────
# Capability → Tool mapping (unchanged from previous version)
# ─────────────────────────────────────────────────────────────────────────────

CAPABILITY_TO_TOOLS: Dict[EvidenceCapability, List[str]] = {
    EvidenceCapability.WorkflowExecution: [
        "get_dag_runs",
        "get_dag_details",
        "get_dag_run_by_id",
        "get_import_errors",
    ],
    EvidenceCapability.TaskLogs: [
        "get_task_instances",
        "get_failed_task_logs",
    ],
    EvidenceCapability.SchedulerHealth: [
        "get_scheduler_health",
        "get_scheduler_heartbeat",
        "get_airflow_version",
        "get_airflow_config",
    ],
    EvidenceCapability.QueueState: [
        "get_pool_stats",
        "get_redis_health",
        "get_redis_queue_depth",
    ],
    EvidenceCapability.DataValidation: [
        "get_task_xcoms",
    ],
    EvidenceCapability.RuntimeMetrics: [
        "get_lambda_errors",
        "get_lambda_duration",
        "get_lambda_throttles",
        "get_lambda_invocations",
    ],
    EvidenceCapability.CloudAudit: [
        "get_lambda_invocation_events",
        "get_iam_policy_changes",
        "get_resource_config_changes",
    ],
    EvidenceCapability.InfrastructureHealth: [
        "get_postgres_connection_count",
        "get_postgres_slow_queries",
    ],
    EvidenceCapability.CostAnomaly: [
        "get_lambda_cost_delta",
    ],
    EvidenceCapability.DependencyState: [
        "detect_cascade_failure",
        "get_all_dags",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Severity Budget
# Severity controls the INVESTIGATION BUDGET (top-N capabilities) only.
# It does NOT influence which domain areas are investigated.
# ─────────────────────────────────────────────────────────────────────────────

SEVERITY_BUDGET: Dict[IncidentSeverity, int] = {
    IncidentSeverity.LOW:      3,
    IncidentSeverity.MEDIUM:   5,
    IncidentSeverity.HIGH:     7,
    IncidentSeverity.CRITICAL: 10,  # effectively all capabilities
}

# Total capabilities available (fallback if budget > available)
_ALL_CAPABILITIES = list(CAPABILITY_TO_TOOLS.keys())


# ─────────────────────────────────────────────────────────────────────────────
# CapabilityScorer — Independent scoring per capability
# Each scorer reads structured IncidentContext fields only.
# ─────────────────────────────────────────────────────────────────────────────

class CapabilityScorer:
    """Base class for scoring a single EvidenceCapability against an IncidentContext."""
    capability: EvidenceCapability
    base_score: float = 0.0

    def score(self, ctx: IncidentContext) -> float:
        return self.base_score


class WorkflowExecutionScorer(CapabilityScorer):
    """Always included — we always need basic workflow state."""
    capability = EvidenceCapability.WorkflowExecution

    def score(self, ctx: IncidentContext) -> float:
        s = 5.0  # Baseline — always needed
        if ctx.workflow_execution_id:
            s += 2.0  # Pinned run — even more valuable
        return s


class TaskLogsScorer(CapabilityScorer):
    """High when we know which node failed."""
    capability = EvidenceCapability.TaskLogs

    def score(self, ctx: IncidentContext) -> float:
        s = 0.0
        if ctx.failed_node_id:
            s += 5.0  # Exact failing node known
        if ctx.execution_state in ("failed", "zombie", "upstream_failed"):
            s += 3.0
        if ctx.retry_number and ctx.retry_number > 0:
            s += 2.0  # Retries suggest persistent task-level issue
        return s


class SchedulerHealthScorer(CapabilityScorer):
    """
    High when the failure is DAG-level (no specific failed node) or a zombie.
    NOT activated purely by severity — that was the previous plan's bug.
    """
    capability = EvidenceCapability.SchedulerHealth

    def score(self, ctx: IncidentContext) -> float:
        s = 0.0
        if ctx.execution_state == "zombie":
            s += 4.0  # Zombie tasks strongly suggest scheduler issues
        if not ctx.failed_node_id:
            s += 3.0  # DAG-level failure, no specific task → check scheduler
        if ctx.trigger_source.value == "orchestrator_callback" and not ctx.failed_node_id:
            s += 2.0  # Orchestrator callback with no failed node = infra signal
        return s


class QueueStateScorer(CapabilityScorer):
    """High when tasks are queued/pending or execution is slow."""
    capability = EvidenceCapability.QueueState

    def score(self, ctx: IncidentContext) -> float:
        s = 0.0
        wid = ctx.workflow_id.lower()
        if "queue" in wid or "pool" in wid or "pending" in wid:
            s += 3.0
        if ctx.execution_state in ("queued", "scheduled"):
            s += 4.0
        if ctx.retry_number and ctx.retry_number > 2:
            s += 2.0  # High retries could be resource contention
        # Medium/high severity with no specific task → could be capacity
        if not ctx.failed_node_id and ctx.severity in (IncidentSeverity.HIGH, IncidentSeverity.CRITICAL):
            s += 1.0
        return s


class DataValidationScorer(CapabilityScorer):
    """High for data quality / XCom investigations."""
    capability = EvidenceCapability.DataValidation

    def score(self, ctx: IncidentContext) -> float:
        s = 0.0
        keywords = ("data", "quality", "validation", "xcom", "empty", "schema", "silent")
        wid = ctx.workflow_id.lower()
        node = (ctx.failed_node_id or "").lower()
        for kw in keywords:
            if kw in wid:
                s += 2.0
            if kw in node:
                s += 2.0
        if ctx.investigation_goal == InvestigationGoal.IMPACT_ANALYSIS:
            s += 3.0
        return s


class RuntimeMetricsScorer(CapabilityScorer):
    """High for Lambda / CloudWatch investigations."""
    capability = EvidenceCapability.RuntimeMetrics

    def score(self, ctx: IncidentContext) -> float:
        s = 0.0
        wid = ctx.workflow_id.lower()
        node = (ctx.failed_node_id or "").lower()
        err = (ctx.orchestrator_error_type or "").lower()
        for kw in ("lambda", "cloud", "throttle", "timeout", "invocation"):
            if kw in wid or kw in node or kw in err:
                s += 3.0
        if ctx.investigation_goal == InvestigationGoal.PERFORMANCE:
            s += 4.0
        return s


class CloudAuditScorer(CapabilityScorer):
    """High for permission / IAM / config drift investigations."""
    capability = EvidenceCapability.CloudAudit

    def score(self, ctx: IncidentContext) -> float:
        s = 0.0
        wid = ctx.workflow_id.lower()
        node = (ctx.failed_node_id or "").lower()
        err = (ctx.orchestrator_error_type or "").lower()
        for kw in ("permission", "iam", "denied", "unauthorized", "forbidden", "policy"):
            if kw in wid or kw in node or kw in err:
                s += 4.0
        # Any Lambda failure should also check CloudTrail
        for kw in ("lambda", "cloud"):
            if kw in wid:
                s += 2.0
        return s


class InfrastructureHealthScorer(CapabilityScorer):
    """High for zombie tasks or DB/infra-related failures."""
    capability = EvidenceCapability.InfrastructureHealth

    def score(self, ctx: IncidentContext) -> float:
        s = 0.0
        if ctx.execution_state == "zombie":
            s += 3.0
        wid = ctx.workflow_id.lower()
        node = (ctx.failed_node_id or "").lower()
        for kw in ("postgres", "db", "database", "connection", "redis", "broker"):
            if kw in wid or kw in node:
                s += 3.0
        if ctx.severity in (IncidentSeverity.HIGH, IncidentSeverity.CRITICAL):
            s += 1.0  # Minor boost for high severity — infra check is cheap
        return s


class CostAnomalyScorer(CapabilityScorer):
    """High when cost analysis is the explicit investigation goal."""
    capability = EvidenceCapability.CostAnomaly

    def score(self, ctx: IncidentContext) -> float:
        s = 0.0
        if ctx.investigation_goal == InvestigationGoal.COST_ANALYSIS:
            s += 5.0
        wid = ctx.workflow_id.lower()
        for kw in ("cost", "sagemaker", "training", "billing", "spend"):
            if kw in wid:
                s += 3.0
        return s


class DependencyStateScorer(CapabilityScorer):
    """High for cascade/upstream failures or impact analysis."""
    capability = EvidenceCapability.DependencyState

    def score(self, ctx: IncidentContext) -> float:
        s = 0.0
        if ctx.execution_state == "upstream_failed":
            s += 5.0  # Explicit cascade signal
        if ctx.investigation_goal == InvestigationGoal.IMPACT_ANALYSIS:
            s += 4.0
        wid = ctx.workflow_id.lower()
        node = (ctx.failed_node_id or "").lower()
        for kw in ("cascade", "upstream", "downstream", "dependency", "etl"):
            if kw in wid or kw in node:
                s += 2.0
        return s


# Registry of all scorers — one per capability
_SCORERS: List[CapabilityScorer] = [
    WorkflowExecutionScorer(),
    TaskLogsScorer(),
    SchedulerHealthScorer(),
    QueueStateScorer(),
    DataValidationScorer(),
    RuntimeMetricsScorer(),
    CloudAuditScorer(),
    InfrastructureHealthScorer(),
    CostAnomalyScorer(),
    DependencyStateScorer(),
]


# ─────────────────────────────────────────────────────────────────────────────
# Tool Resolution
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_tools(capabilities: List[EvidenceCapability]) -> List[str]:
    """Flatten capabilities into a deduplicated ordered list of tool names."""
    tools = []
    seen = set()
    for cap in capabilities:
        for tool in CAPABILITY_TO_TOOLS.get(cap, []):
            if tool not in seen:
                tools.append(tool)
                seen.add(tool)
    return tools


# ─────────────────────────────────────────────────────────────────────────────
# InvestigationPlanner
# ─────────────────────────────────────────────────────────────────────────────

class InvestigationPlanner:
    """
    Context-aware capability ranker.

    1. Score each capability independently against the IncidentContext.
    2. Sort by score descending.
    3. Slice to the severity budget (top-N).
    4. Resolve to tool names.
    """

    def build_plan(self, request: InvestigationRequest) -> InvestigationPlan:
        ctx = request.incident_context

        if ctx is None:
            # Legacy path: create a minimal context from dag_id + reported_symptom
            from backend.investigation.models import IncidentContext, TriggerSource, IncidentSeverity
            ctx = IncidentContext(
                workflow_id=request.dag_id or "unknown",
                execution_state="unknown",
                trigger_source=TriggerSource.MANUAL,
                severity=IncidentSeverity.MEDIUM,
                additional_context={"user_query": request.reported_symptom or ""}
            )

        # Step 1: Score all capabilities independently
        scored: List[Tuple[float, EvidenceCapability]] = []
        for scorer in _SCORERS:
            s = scorer.score(ctx)

            # Apply InvestigationGoal-based boosts
            goal_boost = _goal_boost(scorer.capability, ctx.investigation_goal)
            total = s + goal_boost

            # Always include WorkflowExecution (base score ensures it)
            scored.append((total, scorer.capability))

        # Step 2: Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)

        # Step 3: Apply severity budget
        budget = SEVERITY_BUDGET.get(ctx.severity, 5)
        # Always keep at least WorkflowExecution regardless of budget
        selected_caps = []
        for score, cap in scored:
            if score > 0 or cap == EvidenceCapability.WorkflowExecution:
                selected_caps.append(cap)
            if len(selected_caps) >= budget:
                break

        # Ensure WorkflowExecution is always first
        if EvidenceCapability.WorkflowExecution in selected_caps:
            selected_caps.remove(EvidenceCapability.WorkflowExecution)
        selected_caps = [EvidenceCapability.WorkflowExecution] + selected_caps

        # Step 4: Resolve to tool names
        all_tools = _resolve_tools(selected_caps)

        skill_label = (
            f"Context:{ctx.investigation_goal.value}/"
            f"{ctx.severity.value}/"
            f"budget{budget}"
        )

        return InvestigationPlan(
            skill=skill_label,
            required_capabilities=selected_caps,
            optional_capabilities=[],
            priority=ctx.severity.value,
            parallel_execution=True,
            estimated_tools=all_tools,
        )

    # Kept for backward compatibility
    def select_skill(self, request: InvestigationRequest) -> BaseSkill:
        return InvestigateRetryStormSkill()


def _goal_boost(capability: EvidenceCapability, goal: InvestigationGoal) -> float:
    """
    Deterministic score boost based on InvestigationGoal.
    Keeps goal-routing logic in one auditable place.
    """
    boosts: Dict[InvestigationGoal, Dict[EvidenceCapability, float]] = {
        InvestigationGoal.ROOT_CAUSE: {
            EvidenceCapability.TaskLogs: 2.0,
            EvidenceCapability.WorkflowExecution: 1.0,
        },
        InvestigationGoal.IMPACT_ANALYSIS: {
            EvidenceCapability.DependencyState: 4.0,
            EvidenceCapability.WorkflowExecution: 2.0,
            EvidenceCapability.DataValidation: 2.0,
        },
        InvestigationGoal.COST_ANALYSIS: {
            EvidenceCapability.CostAnomaly: 5.0,
            EvidenceCapability.RuntimeMetrics: 3.0,
        },
        InvestigationGoal.PERFORMANCE: {
            EvidenceCapability.RuntimeMetrics: 4.0,
            EvidenceCapability.InfrastructureHealth: 3.0,
            EvidenceCapability.QueueState: 2.0,
        },
    }
    return boosts.get(goal, {}).get(capability, 0.0)
