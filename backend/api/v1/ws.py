from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import asyncio
import uuid
from backend.api.dependencies import get_investigation_service
from backend.application.investigation_service import InvestigationService
from backend.domain.investigation import InvestigationState
from backend.domain.events import StateChangeEvent

router = APIRouter(prefix="/ws", tags=["WebSockets"])

@router.websocket("/investigations/{id}/stream")
async def investigation_stream(
    websocket: WebSocket,
    id: str,
    service: InvestigationService = Depends(get_investigation_service)
):
    await websocket.accept()
    
    # In Phase 4, we simulate the state machine progression to demonstrate the architecture
    try:
        inv = service.get_investigation(id)
        if not inv:
            await websocket.close(code=1008, reason="Investigation not found")
            return
            
        states_to_simulate = [
            InvestigationState.RUNNING,
            InvestigationState.COLLECTING_EVIDENCE,
            InvestigationState.CORRELATING,
            InvestigationState.GENERATING_TIMELINE,
            InvestigationState.GENERATING_REPORT,
            InvestigationState.WAITING_APPROVAL
        ]
        
        for state in states_to_simulate:
            await asyncio.sleep(1.5)  # Simulate work
            service.update_state(id, state)
            
            # Use our strict contract mapping progress from state
            evt = StateChangeEvent(
                id=f"evt_{uuid.uuid4().hex[:8]}",
                new_state=state.value,
                progress=service.get_investigation(id).progress
            )
            
            # Pydantic json serialization
            await websocket.send_json(evt.model_dump(mode='json'))
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket Error: {e}")
