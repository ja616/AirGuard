from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
from backend.api.dependencies import get_investigation_service
from backend.application.investigation_service import InvestigationService
from backend.domain.investigation import InvestigationState

router = APIRouter(prefix="/metrics", tags=["Metrics"])

class MetricsResponse(BaseModel):
    total_investigations: int
    failed_investigations: int
    completed_investigations: int
    average_duration_seconds: float
    state_counts: Dict[str, int]

@router.get("/", response_model=MetricsResponse)
def get_operational_metrics(
    service: InvestigationService = Depends(get_investigation_service)
):
    """Get real execution metrics based on the repository state."""
    investigations = service.list_investigations(limit=10000)
    
    total = len(investigations)
    state_counts = {}
    for state in InvestigationState:
        state_counts[state.value] = 0
        
    completed = 0
    failed = 0
    total_duration = 0
    duration_count = 0
    
    for inv in investigations:
        state_counts[inv.state.value] = state_counts.get(inv.state.value, 0) + 1
        
        if inv.state == InvestigationState.COMPLETED:
            completed += 1
        elif inv.state == InvestigationState.FAILED:
            failed += 1
            
        if inv.metadata.duration_seconds is not None:
            total_duration += inv.metadata.duration_seconds
            duration_count += 1
            
    avg_duration = total_duration / duration_count if duration_count > 0 else 0.0
    
    return MetricsResponse(
        total_investigations=total,
        failed_investigations=failed,
        completed_investigations=completed,
        average_duration_seconds=round(avg_duration, 2),
        state_counts=state_counts
    )
