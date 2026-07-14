from typing import Optional, List, Dict
from backend.domain.session import SessionState
from backend.infrastructure.repositories.interfaces import ISessionRepository

class MemorySessionRepository(ISessionRepository):
    def __init__(self):
        self._store: Dict[str, SessionState] = {}

    def create(self, session: SessionState) -> SessionState:
        self._store[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[SessionState]:
        return self._store.get(session_id)

    def update(self, session: SessionState) -> SessionState:
        self._store[session.session_id] = session
        return session

    def delete(self, session_id: str) -> bool:
        if session_id in self._store:
            del self._store[session_id]
            return True
        return False

    def get_expired_sessions(self, timeout_minutes: int = 30) -> List[SessionState]:
        return [
            session for session in self._store.values()
            if session.is_expired(timeout_minutes)
        ]
