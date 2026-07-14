"""
Strict Pydantic models defining Ground Truth and Evaluation Results 
for synthetic operational incidents.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.core.constants import ConfidenceLevel

class GroundTruth(BaseModel):
    """
    Defines the deterministic answers the investigation pipeline 
    is expected to find.
    """
    expected_root_cause: str = Field(description="Substring or exact match expected in final RCA")
    expected_primary_evidence_types: List[str] = Field(description="Class names of expected evidence (e.g., 'TaskEvidence')")
    expected_timeline_length_min: int = Field(description="Minimum number of events required in timeline")
    expected_confidence_level: ConfidenceLevel = Field(description="Expected final confidence level")
    expected_blast_radius_workflows: List[str] = Field(description="DAG IDs expected to be flagged as affected")

class EvaluationResult(BaseModel):
    """
    The final output of running a scenario through the framework.
    """
    scenario_name: str
    passed: bool
    root_cause_match: bool
    timeline_sufficient: bool
    confidence_calibrated: bool
    blast_radius_accurate: bool
    actual_root_cause: str
    actual_confidence_level: str
    errors: List[str] = Field(default_factory=list, description="Reasons for failing specific checks")
