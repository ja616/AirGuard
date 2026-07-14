"""
Strongly typed models for the AirGuard Incident Taxonomy.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.core.constants import IncidentCategory

class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class IncidentDefinition(BaseModel):
    """
    The canonical definition of an operational incident that AirGuard can investigate.
    This strictly follows the frozen architecture principles.
    """
    id: str = Field(description="Unique identifier, e.g., 'INC-SCHED-001'")
    name: str = Field(description="Human readable name")
    description: str = Field(description="Detailed description of the incident type")
    severity: SeverityLevel
    category: IncidentCategory
    supported: bool = Field(default=True, description="Whether AirGuard currently supports this incident")
    
    observable_symptoms: List[str] = Field(description="What the user or Datadog sees")
    required_evidence: List[str] = Field(description="Facts needed to prove the incident")
    required_tools: List[str] = Field(description="Deterministic tools needed to gather evidence")
    
    correlation_strategy: str = Field(description="How to connect Airflow and AWS telemetry")
    confidence_strategy: str = Field(description="How to calculate confidence score (no LLMs)")
    
    possible_root_causes: List[str] = Field(description="Known root causes")
    recommended_remediation: List[str] = Field(description="Actionable recommendations")
    business_impact: str = Field(description="Why this matters")
    false_positives: List[str] = Field(description="Scenarios where symptoms appear but no incident exists")
    future_extensions: List[str] = Field(description="Ideas for future capabilities")
