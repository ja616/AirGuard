from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from backend.api.dependencies import get_investigation_service, get_current_user, CurrentUser
from backend.application.investigation_service import InvestigationService
from backend.domain.investigation import Investigation, InvestigationState

router = APIRouter(prefix="/investigations", tags=["Investigations"])


class TriggerInvestigationRequest(BaseModel):
    """
    Unified trigger payload. Accepts either:
      - Structured incident context (new path)
      - Legacy user_query string (backward compatible)

    When both are provided, structured fields take priority.
    """
    # Required
    dag_id: str

    # NEW: Structured incident context fields
    workflow_execution_id: Optional[str] = None   # dag_run_id equivalent
    failed_node_id: Optional[str] = None           # task_id equivalent
    execution_timestamp: Optional[datetime] = None
    severity: Optional[str] = None                 # critical/high/medium/low
    trigger_source: Optional[str] = None           # orchestrator_callback/manual/api/slack
    environment: Optional[str] = "prod"            # dev/staging/prod
    investigation_goal: Optional[str] = None       # root_cause/impact_analysis/cost_analysis/performance
    execution_state: Optional[str] = None          # failed/upstream_failed/zombie
    retry_number: Optional[int] = None
    orchestrator_error_type: Optional[str] = None
    additional_context: Optional[dict] = None

    # LEGACY: Free-text query (still accepted)
    user_query: Optional[str] = None


# Keep old name as alias for any existing integrations
CreateInvestigationRequest = TriggerInvestigationRequest


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ApprovalRequest(BaseModel):
    action: str
    reason: str


@router.post("/", response_model=Investigation)
def create_investigation(
    req: TriggerInvestigationRequest,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
    service: InvestigationService = Depends(get_investigation_service)
):
    """Start a new investigation. Accepts structured IncidentContext or legacy user_query."""
    inv = service.create_investigation(started_by=user.id)

    # Route to structured path if any context fields are provided
    has_structured_context = any([
        req.workflow_execution_id,
        req.failed_node_id,
        req.severity,
        req.execution_state,
        req.investigation_goal,
    ])

    if has_structured_context:
        from backend.investigation.models import (
            IncidentContext, IncidentSeverity, TriggerSource, InvestigationGoal
        )
        try:
            severity = IncidentSeverity(req.severity) if req.severity else IncidentSeverity.MEDIUM
        except ValueError:
            severity = IncidentSeverity.MEDIUM
        try:
            trigger_src = TriggerSource(req.trigger_source) if req.trigger_source else TriggerSource.API
        except ValueError:
            trigger_src = TriggerSource.API
        try:
            goal = InvestigationGoal(req.investigation_goal) if req.investigation_goal else InvestigationGoal.ROOT_CAUSE
        except ValueError:
            goal = InvestigationGoal.ROOT_CAUSE

        ctx = IncidentContext(
            workflow_id=req.dag_id,
            workflow_execution_id=req.workflow_execution_id,
            failed_node_id=req.failed_node_id,
            execution_timestamp=req.execution_timestamp or __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
            severity=severity,
            trigger_source=trigger_src,
            environment=req.environment or "prod",  # type: ignore[arg-type]
            investigation_goal=goal,
            execution_state=req.execution_state,
            retry_number=req.retry_number,
            orchestrator_error_type=req.orchestrator_error_type,
            additional_context=req.additional_context or {},
        )
        background_tasks.add_task(
            service.execute_investigation_pipeline_async_context,
            inv.id,
            ctx,
        )
    else:
        # Legacy path: user_query or empty string
        user_query = req.user_query or f"Investigation triggered for DAG: {req.dag_id}"
        background_tasks.add_task(
            service.execute_investigation_pipeline_async,
            inv.id,
            req.dag_id,
            user_query,
        )

    return inv

@router.get("/", response_model=List[Investigation])
def list_investigations(
    limit: int = 100,
    offset: int = 0,
    service: InvestigationService = Depends(get_investigation_service)
):
    """List all investigations."""
    return service.list_investigations(limit=limit, offset=offset)

@router.get("/{id}", response_model=Investigation)
def get_investigation(
    id: str,
    service: InvestigationService = Depends(get_investigation_service)
):
    """Get investigation details and metadata."""
    inv = service.get_investigation(id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv

@router.get("/{id}/timeline")
def get_timeline(
    id: str,
    service: InvestigationService = Depends(get_investigation_service)
):
    """Get timeline artifact for an investigation."""
    inv = service.get_investigation(id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    for artifact in inv.artifacts:
        if artifact.type == "timeline":
            return artifact
    raise HTTPException(status_code=404, detail="Timeline not generated yet")

@router.get("/{id}/evidence")
def get_evidence(
    id: str,
    service: InvestigationService = Depends(get_investigation_service)
):
    """Get evidence for an investigation."""
    inv = service.get_investigation(id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    for artifact in inv.artifacts:
        if artifact.type == "evidence":
            return artifact
    raise HTTPException(status_code=404, detail="Evidence not generated yet")

@router.get("/{id}/graph")
def get_graph(
    id: str,
    service: InvestigationService = Depends(get_investigation_service)
):
    """Get correlation graph for an investigation."""
    inv = service.get_investigation(id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    for artifact in inv.artifacts:
        if artifact.type == "graph":
            return artifact
    raise HTTPException(status_code=404, detail="Graph not generated yet")

@router.get("/{id}/report")
def get_report(
    id: str,
    service: InvestigationService = Depends(get_investigation_service)
):
    """Get operational report for an investigation."""
    inv = service.get_investigation(id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    for artifact in inv.artifacts:
        if artifact.type == "report":
            return artifact
    raise HTTPException(status_code=404, detail="Report not generated yet")

@router.post("/{id}/approve")
def approve_action(
    id: str,
    req: ApprovalRequest,
    user: CurrentUser = Depends(get_current_user),
    service: InvestigationService = Depends(get_investigation_service)
):
    """Approve or reject a pending action."""
    inv = service.get_investigation(id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    if inv.state != InvestigationState.READY_FOR_REVIEW:
        raise HTTPException(status_code=400, detail="Investigation not waiting for approval")
        
    if req.action.lower() == "approve":
        service.update_state(id, InvestigationState.COMPLETED)
    else:
        service.update_state(id, InvestigationState.FAILED)
        
    return {"status": req.action, "timestamp": "now"}

@router.post("/{id}/chat")
def chat(
    id: str,
    req: ChatRequest,
    user: CurrentUser = Depends(get_current_user)
):
    """Stateful chat regarding an investigation."""
    return {"reply": "Chat endpoint stub", "session_id": req.session_id}
