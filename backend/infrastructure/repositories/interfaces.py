from abc import ABC, abstractmethod
from typing import Optional, List
from backend.domain.session import SessionState
from backend.domain.investigation import Investigation

class ISessionRepository(ABC):
    @abstractmethod
    def create(self, session: SessionState) -> SessionState:
        pass

    @abstractmethod
    def get(self, session_id: str) -> Optional[SessionState]:
        pass

    @abstractmethod
    def update(self, session: SessionState) -> SessionState:
        pass

    @abstractmethod
    def delete(self, session_id: str) -> bool:
        pass

    @abstractmethod
    def get_expired_sessions(self, timeout_minutes: int = 30) -> List[SessionState]:
        pass

class IInvestigationRepository(ABC):
    @abstractmethod
    def create(self, investigation: Investigation) -> Investigation:
        pass

    @abstractmethod
    def get(self, investigation_id: str) -> Optional[Investigation]:
        pass

    @abstractmethod
    def update(self, investigation: Investigation) -> Investigation:
        pass

    @abstractmethod
    def list(self, limit: int = 100, offset: int = 0) -> List[Investigation]:
        pass
