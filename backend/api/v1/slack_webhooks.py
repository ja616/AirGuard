from fastapi import APIRouter, Request, HTTPException
from backend.integrations.registry import registry
import json
import logging

router = APIRouter(prefix="/api/v1/slack", tags=["slack"])
logger = logging.getLogger(__name__)

@router.post("/events")
async def handle_slack_interaction(request: Request):
    """
    Handles Slack interactive callbacks (e.g. from Block Kit buttons).
    Slack sends a URL-encoded POST with a 'payload' field containing JSON.
    """
    try:
        form_data = await request.form()
        payload_str = form_data.get("payload")
        if not payload_str:
            raise HTTPException(status_code=400, detail="Missing payload")

        payload = json.loads(payload_str)
        
        if payload.get("type") == "block_actions":
            actions = payload.get("actions", [])
            for action in actions:
                action_id = action.get("action_id", "")
                value = action.get("value", "unknown")
                user = payload.get("user", {}).get("username", "operator")
                
                slack_client = registry.get_slack_client()
                
                if action_id.startswith("approve_"):
                    logger.info(f"Received approval for {value} from {user}")
                    slack_client.post_message(f"✅ Approved investigation {value} by @{user}")
                elif action_id.startswith("reject_"):
                    logger.info(f"Received rejection for {value} from {user}")
                    slack_client.post_message(f"❌ Rejected investigation {value} by @{user}")
                    
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Failed to process Slack event: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
