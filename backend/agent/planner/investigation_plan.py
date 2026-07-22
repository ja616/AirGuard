from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class EvidenceCapability(str, Enum):
    WorkflowExecution = "WorkflowExecution"
    TaskLogs = "TaskLogs"
    RuntimeMetrics = "RuntimeMetrics"
    SchedulerHealth = "SchedulerHealth"
    CloudAudit = "CloudAudit"
    InfrastructureHealth = "InfrastructureHealth"
    CostTelemetry = "CostTelemetry"
    WorkerHealth = "WorkerHealth"
    QueueState = "QueueState"
    ResourceMetadata = "ResourceMetadata"
    DataValidation = "DataValidation"
    DependencyState = "DependencyState"
    CostAnomaly = "CostAnomaly"

class InvestigationPlan(BaseModel):
    skill: str
    required_capabilities: List[EvidenceCapability]
    optional_capabilities: List[EvidenceCapability]
    priority: str = "medium"
    parallel_execution: bool = True
    estimated_tools: List[str] = Field(default_factory=list, description="Tools mapped from capabilities by the planner")
