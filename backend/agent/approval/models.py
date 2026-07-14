from pydantic import BaseModel, Field

class ProposedAction(BaseModel):
    """
    A structured, mandatory proposal required before the Agent can execute a write-action.
    This guarantees zero autonomous remediation without explicit human consent.
    """
    id: str
    action_type: str = Field(description="e.g., PAUSE_DAG, CREATE_JIRA, DISABLE_SCHEDULE")
    reason: str = Field(description="Why this action is recommended based on the OperationalReport.")
    expected_impact: str = Field(description="What will happen if approved.")
    risk_level: str = Field(description="LOW, MEDIUM, HIGH")
    payload: dict = Field(default_factory=dict, description="The technical payload to execute.")
    status: str = Field(default="PENDING", description="PENDING, APPROVED, REJECTED")
