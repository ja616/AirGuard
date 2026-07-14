from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class BaseWebSocketEvent(BaseModel):
    id: str
    type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    progress: int
    payload: Dict[str, Any] = Field(default_factory=dict)

class EvidenceCollectionEvent(BaseWebSocketEvent):
    type: str = "evidence_collection_completed"
    source: str

class StateChangeEvent(BaseWebSocketEvent):
    type: str = "state_changed"
    new_state: str
