import uuid
from typing import Optional, List
from backend.domain.session import SessionState
from backend.infrastructure.repositories.interfaces import ISessionRepository

class SessionService:
    def __init__(self, repository: ISessionRepository):
        self.repository = repository

    def create_session(self, user_id: str) -> SessionState:
        session_id = str(uuid.uuid4())
        session = SessionState(session_id=session_id, user_id=user_id)
        return self.repository.create(session)

    def get_session(self, session_id: str) -> Optional[SessionState]:
        session = self.repository.get(session_id)
        if session and not session.is_expired():
            session.touch()
            return self.repository.update(session)
        return None

    def link_investigation(self, session_id: str, investigation_id: str) -> Optional[SessionState]:
        session = self.get_session(session_id)
        if session:
            session.active_investigation_id = investigation_id
            session.touch()
            return self.repository.update(session)
        return None

    def add_conversation_turn(self, session_id: str, role: str, content: str) -> Optional[SessionState]:
        session = self.get_session(session_id)
        if session:
            session.conversation_history.append({"role": role, "content": content})
            session.touch()
            return self.repository.update(session)
        return None

    def cleanup_expired_sessions(self, timeout_minutes: int = 30) -> int:
        expired = self.repository.get_expired_sessions(timeout_minutes)
        count = 0
        for session in expired:
            if self.repository.delete(session.session_id):
                count += 1
        return count
