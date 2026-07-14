from pydantic import BaseModel, Field
from typing import List

class OperationalReport(BaseModel):
    executive_summary: str
    incident_classification: str
    timeline: List[dict] = Field(default_factory=list)
    evidence_summary: str
    blast_radius: str
    root_cause: str
    confidence: str
    recommendations: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
