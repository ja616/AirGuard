"""
AgentCore Harness.
Guarantees strict boundaries around deterministic execution.
"""
import uuid
from typing import Dict
from backend.agent.harness.memory import InvestigationMemory

class AgentCoreHarness:
    """
    Manages session lifecycle, memory scoping, and explicit boundaries.
    The LLM interacts through this harness; it cannot access the core directly.
    """
    def __init__(self):
        # In production, this would be backed by Redis or DynamoDB with TTLs
        self.active_sessions: Dict[str, InvestigationMemory] = {}

    def create_session(self, initial_query: str) -> str:
        """Initializes a hygienic, empty investigation context."""
        session_id = str(uuid.uuid4())
        memory = InvestigationMemory(
            session_id=session_id,
            original_query=initial_query
        )
        memory.add_message("user", initial_query)
        self.active_sessions[session_id] = memory
        return session_id

    def get_memory(self, session_id: str) -> InvestigationMemory:
        """Retrieves the strict state for the current investigation."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found or has expired.")
        return self.active_sessions[session_id]
        
    def end_session(self, session_id: str) -> None:
        """
        Enforces strict memory scoping.
        Once an investigation concludes, active memory is wiped to prevent hallucination 
        carry-over into future incidents.
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
