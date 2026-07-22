"""
AWS SNS Webhook Endpoint
========================
Handles incoming Amazon SNS notifications, specifically designed for
AWS Cost Anomaly Detection alerts.

Automatically handles SNS SubscriptionConfirmation requests.
Maps Cost Anomaly Notifications to AirGuard's IncidentContext and triggers an investigation.
"""
import json
import logging
import requests
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel

from backend.investigation.models import (
    IncidentContext, 
    IncidentSeverity, 
    InvestigationGoal, 
    TriggerSource
)
from backend.api.dependencies import get_investigation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/aws", tags=["AWS Integration"])

@router.post("/sns")
async def sns_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_amz_sns_message_type: str = Header(None)
):
    """
    Receives SNS payloads. 
    Handles both SubscriptionConfirmation and Notification types.
    """
    try:
        payload_bytes = await request.body()
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    message_type = x_amz_sns_message_type or payload.get("Type")

    if not message_type:
        raise HTTPException(status_code=400, detail="Missing SNS message type")

    # 1. Handle Subscription Confirmation
    if message_type == "SubscriptionConfirmation":
        subscribe_url = payload.get("SubscribeURL")
        if subscribe_url:
            logger.info(f"Confirming SNS subscription via URL: {subscribe_url}")
            # Fire-and-forget GET request to confirm using standard requests
            background_tasks.add_task(requests.get, subscribe_url)
            return {"status": "Subscription confirmed"}
        return {"status": "Missing SubscribeURL"}

    # 2. Handle Notifications
    if message_type == "Notification":
        message_str = payload.get("Message", "{}")
        try:
            # AWS Cost Anomaly messages are typically stringified JSON inside the SNS Message
            anomaly_data = json.loads(message_str)
        except json.JSONDecodeError:
            # Fallback for plain text SNS messages
            anomaly_data = {"raw_message": message_str}

        anomaly_id = anomaly_data.get("anomalyId", "unknown_anomaly")
        impact = anomaly_data.get("impact", {})
        total_impact = impact.get("totalImpact", 0.0)
        
        # Determine Severity based on cost impact
        severity = IncidentSeverity.MEDIUM
        if isinstance(total_impact, (int, float)) and total_impact > 1000:
            severity = IncidentSeverity.HIGH
        if isinstance(total_impact, (int, float)) and total_impact > 5000:
            severity = IncidentSeverity.CRITICAL

        # Map to IncidentContext
        incident_context = IncidentContext(
            workflow_id=f"aws_cost_anomaly_{anomaly_id}",
            execution_state="anomaly_detected",
            trigger_source=TriggerSource.API,
            severity=severity,
            investigation_goal=InvestigationGoal.COST_ANALYSIS,
            additional_context={
                "anomaly_details": json.dumps(anomaly_data),
                "sns_topic_arn": payload.get("TopicArn", "")
            }
        )

        # Trigger Investigation
        service = get_investigation_service()
        inv = service.create_investigation(
            started_by="aws_sns_cost_anomaly",
            airflow_environment="aws_cloud"
        )
        background_tasks.add_task(
            service.execute_investigation_pipeline_async_context,
            inv.id,
            incident_context,
        )

        logger.info(
            f"Cost Anomaly Investigation {inv.id} started for anomaly '{anomaly_id}'. "
            f"Impact: {total_impact}, Severity: {severity.value}"
        )

        return {
            "investigation_id": inv.id,
            "status": "Investigation triggered",
            "anomaly_id": anomaly_id
        }

    # Ignore other SNS message types (like UnsubscribeConfirmation)
    return {"status": f"Ignored message type: {message_type}"}
