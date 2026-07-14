"""
First-class domain models for Operational Expertise.
This represents the 'brain' of the SRE encoded into strict rules.
"""
from pydantic import BaseModel, Field
from typing import List

class InvestigationQuestion(BaseModel):
    """
    A specific question the Skill must answer before proceeding to correlation.
    """
    question: str = Field(description="The human-readable question (e.g., 'Was deployment involved?')")
    required_evidence_type: str = Field(description="The Domain Object needed (e.g., 'CloudTrailEvidence')")
    tool_capability_needed: str = Field(description="The capability group needed (e.g., 'collection')")

class BlastRadiusRule(BaseModel):
    """
    Rules dictating how the investigation should expand its scope.
    """
    dimension: str = Field(description="What to look at next (e.g., 'downstream_workflows')")
    expansion_strategy: str = Field(description="How to find them (e.g., 'dependency_graph_traversal')")

class OperationalPlaybook(BaseModel):
    """
    The complete, structured investigation strategy for a specific incident.
    """
    incident_id: str
    name: str
    description: str
    symptoms: List[str]
    required_evidence: List[str]
    
    # The crucial addition: mandatory questions
    investigation_questions: List[InvestigationQuestion]
    
    typical_causes: List[str]
    recommended_correlation_strategy: str
    confidence_rules: str
    recommended_remediation: List[str]
    
    # Scope expansion logic
    blast_radius_rules: List[BlastRadiusRule]
    
    future_extensions: List[str]
