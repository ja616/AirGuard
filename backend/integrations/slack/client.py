import time
import requests
from typing import Dict, Any, List
from backend.integrations.core.interfaces import ISlackClient
from backend.integrations.core.retry import with_retry
from backend.integrations.core.telemetry import with_telemetry
from backend.integrations.core.config import config

class RestSlackClient(ISlackClient):
    def __init__(self):
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {config.slack_bot_token}",
            "Content-Type": "application/json"
        }
        self.default_channel = config.slack_channel_id

    @with_telemetry("Slack", "health")
    def health(self) -> bool:
        try:
            response = requests.post(f"{self.base_url}/auth.test", headers=self.headers, timeout=5)
            return response.json().get("ok", False)
        except Exception:
            return False

    def ping(self) -> float:
        start = time.time()
        self.health()
        return (time.time() - start) * 1000

    def capabilities(self) -> List[str]:
        return ["messaging", "threads", "block_kit"]

    @with_retry(max_retries=3)
    @with_telemetry("Slack", "post_message")
    def post_message(self, text: str, channel: str = None) -> Dict[str, Any]:
        payload = {
            "channel": channel or self.default_channel,
            "text": text
        }
        response = requests.post(f"{self.base_url}/chat.postMessage", headers=self.headers, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()

    @with_retry(max_retries=3)
    @with_telemetry("Slack", "create_thread")
    def create_thread(self, text: str, channel: str = None) -> Dict[str, Any]:
        return self.post_message(text, channel)

    @with_retry(max_retries=3)
    @with_telemetry("Slack", "reply_in_thread")
    def reply_in_thread(self, text: str, thread_ts: str, channel: str = None) -> Dict[str, Any]:
        payload = {
            "channel": channel or self.default_channel,
            "text": text,
            "thread_ts": thread_ts
        }
        response = requests.post(f"{self.base_url}/chat.postMessage", headers=self.headers, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()

    @with_retry(max_retries=3)
    @with_telemetry("Slack", "send_report_blocks")
    def send_report_blocks(self, blocks: List[Dict[str, Any]], channel: str = None) -> Dict[str, Any]:
        payload = {
            "channel": channel or self.default_channel,
            "blocks": blocks,
            "text": "Fallback text for notification"
        }
        response = requests.post(f"{self.base_url}/chat.postMessage", headers=self.headers, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()

    @with_retry(max_retries=3)
    @with_telemetry("Slack", "send_approval_blocks")
    def send_approval_blocks(self, blocks: List[Dict[str, Any]], channel: str = None) -> Dict[str, Any]:
        return self.send_report_blocks(blocks, channel)
