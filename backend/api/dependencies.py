"""
Dependency Injection definitions for FastAPI.
"""
from typing import Generator
from pydantic import BaseModel

from backend.infrastructure.repositories.memory_session import MemorySessionRepository
from backend.infrastructure.repositories.memory_investigation import MemoryInvestigationRepository
from backend.application.session_service import SessionService
from backend.application.investigation_service import InvestigationService

class CurrentUser(BaseModel):
    id: str
    role: str

# In-memory singletons for Phase 4
_session_repo = MemorySessionRepository()
_investigation_repo = MemoryInvestigationRepository()
_session_service = SessionService(_session_repo)
_investigation_service = InvestigationService(_investigation_repo)

def get_current_user() -> CurrentUser:
    """
    Stub authentication for Phase 4.
    """
    return CurrentUser(id="local-dev", role="admin")

def get_session_service() -> SessionService:
    return _session_service

def get_investigation_service() -> InvestigationService:
    return _investigation_service
