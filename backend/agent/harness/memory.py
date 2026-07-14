"""
Investigation-scoped Session Memory.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from backend.investigation.models import OperationalReport
from backend.evidence.models import Evidence

class ChatMessage(BaseModel):
    """A single turn in the conversation."""
    role: str = Field(description="'user' or 'agent'")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class InvestigationMemory(BaseModel):
    """
    Strictly scoped to a single incident to prevent cross-contamination.
    Serves as the rigid data structure backing the AgentCore session.
    """
    session_id: str
    original_query: str
    chat_history: List[ChatMessage] = Field(default_factory=list)
    
    # Execution Tracking
    executed_skills: List[str] = Field(default_factory=list, description="Skills invoked by the Planner")
    collected_evidence: List[Evidence] = Field(default_factory=list, description="Raw deterministic evidence")
    
    # The final unchangeable facts from the deterministic core
    operational_report: Optional[OperationalReport] = None
    
    def add_message(self, role: str, content: str):
        self.chat_history.append(ChatMessage(role=role, content=content))
