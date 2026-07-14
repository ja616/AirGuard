from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
from backend.integrations.registry import registry

router = APIRouter(prefix="/health", tags=["Health"])

class HealthResponse(BaseModel):
    status: str
    backend: str
    database: str
    airflow: str
    aws: str
    slack: str

@router.get("/", response_model=HealthResponse)
def health_check():
    """Detailed health check for all subsystems."""
    
    # Check Airflow
    try:
        airflow_status = "Healthy" if registry.get_airflow_client().health() else "Unavailable"
    except Exception:
        airflow_status = "Unavailable"
        
    # Check AWS
    try:
        aws_status = "Healthy" if registry.get_aws_registry().get_cloudwatch_client().health() else "Unavailable"
    except Exception:
        aws_status = "Unavailable"
        
    # Check Slack
    try:
        slack_status = "Healthy" if registry.get_slack_client().health() else "Unavailable"
    except Exception:
        slack_status = "Unavailable"
        
    # Overall database (Memory for now, so always healthy)
    db_status = "Healthy"
    backend_status = "Healthy"
    
    overall = "Healthy"
    if any(s == "Unavailable" for s in [airflow_status, aws_status, slack_status]):
        overall = "Degraded"
    if all(s == "Unavailable" for s in [airflow_status, aws_status, slack_status]):
        overall = "Unavailable"
        
    return HealthResponse(
        status=overall,
        backend=backend_status,
        database=db_status,
        airflow=airflow_status,
        aws=aws_status,
        slack=slack_status
    )
