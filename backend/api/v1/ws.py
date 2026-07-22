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
    
    try:
        inv = service.get_investigation(id)
        if not inv:
            await websocket.close(code=1008, reason="Investigation not found")
            return
            
        from backend.infrastructure.redis_pubsub import redis_pubsub
        
        # If the investigation is already completed or failed, we can just send the final state and close
        if inv.state in [InvestigationState.COMPLETED, InvestigationState.FAILED]:
            evt = StateChangeEvent(
                id=f"evt_{uuid.uuid4().hex[:8]}",
                new_state=inv.state.value,
                progress=inv.progress
            )
            await websocket.send_json(evt.model_dump(mode='json'))
            return
            
        # Callback for incoming Redis messages
        async def on_message(data: dict):
            await websocket.send_json(data)
            
        # Start subscribing to real-time events
        await redis_pubsub.subscribe(f"investigation:{id}:state", on_message)
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket Error: {e}")
