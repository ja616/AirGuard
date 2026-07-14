from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
from backend.integrations.registry import registry
from backend.integrations.core.config import config

router = APIRouter(prefix="/api/v1/connections", tags=["connections"])

class IntegrationStatus(BaseModel):
    status: str
    latency_ms: float
    capabilities: List[str]
    details: Dict[str, Any] = {}

class ConnectionsResponse(BaseModel):
    status: str
    integrations: Dict[str, IntegrationStatus]

@router.get("", response_model=ConnectionsResponse)
def get_connections():
    overall_status = "healthy"
    integrations_status = {}

    # Airflow check
    try:
        client = registry.get_airflow_client()
        is_healthy = client.health()
        latency = client.ping()
        capabilities = client.capabilities()
        version = client.get_version() if is_healthy else "unknown"
        
        integrations_status["airflow"] = IntegrationStatus(
            status="connected" if is_healthy else "degraded",
            latency_ms=latency,
            capabilities=capabilities,
            details={"version": version}
        )
        if not is_healthy: overall_status = "degraded"
    except Exception as e:
        overall_status = "degraded"
        integrations_status["airflow"] = IntegrationStatus(
            status="disconnected", latency_ms=0.0, capabilities=[], details={"error": str(e)}
        )

    # AWS check (Using CloudWatch as a proxy for basic reachability)
    try:
        aws = registry.get_aws_registry()
        cw = aws.get_cloudwatch_client()
        is_healthy = cw.health()
        latency = cw.ping()
        capabilities = cw.capabilities()
        
        integrations_status["aws"] = IntegrationStatus(
            status="connected" if is_healthy else "degraded",
            latency_ms=latency,
            capabilities=capabilities,
            details={"profile": config.aws_profile, "region": config.aws_region}
        )
        if not is_healthy: overall_status = "degraded"
    except Exception as e:
        overall_status = "degraded"
        integrations_status["aws"] = IntegrationStatus(
            status="disconnected", latency_ms=0.0, capabilities=[], details={"error": str(e)}
        )

    # Slack check
    try:
        slack = registry.get_slack_client()
        is_healthy = slack.health()
        latency = slack.ping()
        capabilities = slack.capabilities()
        
        integrations_status["slack"] = IntegrationStatus(
            status="connected" if is_healthy else "degraded",
            latency_ms=latency,
            capabilities=capabilities,
            details={}
        )
        if not is_healthy: overall_status = "degraded"
    except Exception as e:
        overall_status = "degraded"
        integrations_status["slack"] = IntegrationStatus(
            status="disconnected", latency_ms=0.0, capabilities=[], details={"error": str(e)}
        )

    return ConnectionsResponse(status=overall_status, integrations=integrations_status)
