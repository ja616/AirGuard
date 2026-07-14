"""
Environment configuration for the deterministic engine.
"""
import os
from pydantic import BaseModel, Field

class Settings(BaseModel):
    environment: str = Field(default=os.getenv("AIRGUARD_ENV", "development"))
    log_level: str = Field(default=os.getenv("AIRGUARD_LOG_LEVEL", "INFO"))
    aws_region: str = Field(default=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    
settings = Settings()
