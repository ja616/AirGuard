from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

class SessionState(BaseModel):
    session_id: str
    user_id: str
    active_investigation_id: Optional[str] = None
    executed_skills: List[str] = Field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        expiration_time = self.updated_at + timedelta(minutes=timeout_minutes)
        return datetime.now(timezone.utc) > expiration_time

    def touch(self):
        self.updated_at = datetime.now(timezone.utc)
