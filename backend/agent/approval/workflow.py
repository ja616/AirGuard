import uuid
from typing import Dict
from backend.agent.approval.models import ProposedAction

class ApprovalGatekeeper:
    """
    The physical gatekeeper for the human-in-the-loop requirement. 
    Halts execution of any proposed remediations until explicitly approved by a human.
    """
    def __init__(self):
        # In production, this state lives in a DB like DynamoDB
        self.pending_actions: Dict[str, ProposedAction] = {}
        
    def propose_action(self, action_type: str, reason: str, impact: str, risk: str, payload: dict) -> ProposedAction:
        """
        Agent calls this when it wants to remediate. It must yield to the user immediately after.
        """
        action_id = str(uuid.uuid4())
        action = ProposedAction(
            id=action_id,
            action_type=action_type,
            reason=reason,
            expected_impact=impact,
            risk_level=risk,
            payload=payload
        )
        self.pending_actions[action_id] = action
        return action
        
    def approve_action(self, action_id: str) -> bool:
        """Human operator explicitly calls this."""
        if action_id not in self.pending_actions:
            raise ValueError(f"Action {action_id} not found.")
            
        action = self.pending_actions[action_id]
        if action.status != "PENDING":
            return False
            
        action.status = "APPROVED"
        
        # --- DETERMINISTIC EXECUTION ---
        # Here, the rigid action payload is passed to the deterministic tool layer.
        # e.g., AirflowClient.pause_dag(action.payload["dag_id"])
        
        return True

    def reject_action(self, action_id: str) -> bool:
        """Human operator rejects the proposed action."""
        if action_id not in self.pending_actions:
            raise ValueError(f"Action {action_id} not found.")
            
        action = self.pending_actions[action_id]
        action.status = "REJECTED"
        return True
