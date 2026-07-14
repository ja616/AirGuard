from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any
from pydantic import BaseModel

from backend.api.dependencies import get_investigation_service, get_current_user, CurrentUser
from backend.application.investigation_service import InvestigationService
from backend.domain.investigation import Investigation, InvestigationState

router = APIRouter(prefix="/investigations", tags=["Investigations"])

class CreateInvestigationRequest(BaseModel):
    dag_id: str
    user_query: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ApprovalRequest(BaseModel):
    action: str
    reason: str

from fastapi import BackgroundTasks

@router.post("/", response_model=Investigation)
def create_investigation(
    req: CreateInvestigationRequest,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
    service: InvestigationService = Depends(get_investigation_service)
):
    """Start a new investigation."""
    inv = service.create_investigation(started_by=user.id)
    background_tasks.add_task(service.execute_investigation_pipeline_async, inv.id, req.dag_id, req.user_query)
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
    return {"message": "Evidence endpoint stub"}

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
    
    if inv.state != InvestigationState.WAITING_APPROVAL:
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
