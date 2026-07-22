import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv(".env.local")

from backend.integrations.slack.client import RestSlackClient
import backend.integrations.core.config as cfg

slack = RestSlackClient()
try:
    print(f"Token starting with: {cfg.config.slack_bot_token[:10] if cfg.config.slack_bot_token else 'None'}")
    res = slack.post_message("Test message from test script")
    print("Success!", res)
except Exception as e:
    print("Failed!", str(e))
