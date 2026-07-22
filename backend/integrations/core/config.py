import os
from enum import Enum
from pydantic import BaseModel

class EnvironmentProfile(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"

class IntegrationConfig(BaseModel):
    environment: EnvironmentProfile = EnvironmentProfile.LOCAL
    
    # Airflow Config
    airflow_api_url: str = "http://localhost:8080/api/v1"
    airflow_username: str = "admin"
    airflow_password: str = "admin"
    
    # AWS Config
    aws_region: str = "us-east-1"
    aws_profile: str = "default"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    
    # Slack Config
    slack_bot_token: str = ""
    slack_channel_id: str = ""

    # Webhook Auth
    airguard_webhook_token: str = ""  # X-AirGuard-Token for /api/v1/airflow/webhook

    @classmethod
    def load_from_env(cls) -> "IntegrationConfig":
        env = os.getenv("AIRGUARD_ENV", "local")
        return cls(
            environment=EnvironmentProfile(env),
            airflow_api_url=os.getenv("AIRFLOW_API_URL", "http://localhost:8080/api/v1"),
            airflow_username=os.getenv("AIRFLOW_USERNAME", "admin"),
            airflow_password=os.getenv("AIRFLOW_PASSWORD", "admin"),
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            aws_profile=os.getenv("AWS_PROFILE", "default"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            slack_bot_token=os.getenv("SLACK_BOT_TOKEN", ""),
            slack_channel_id=os.getenv("SLACK_CHANNEL_ID", ""),
            airguard_webhook_token=os.getenv("AIRGUARD_WEBHOOK_TOKEN", ""),
        )

# Global singleton configuration
config = IntegrationConfig.load_from_env()
