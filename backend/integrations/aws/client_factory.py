import os
import boto3
import threading
os.environ.pop("AWS_PROFILE", None)
from backend.integrations.core.config import config

_client_lock = threading.Lock()

def get_boto3_client(service_name: str, region_name: str = None):
    """
    Centralized factory to instantiate boto3 clients securely,
    injecting credentials from the configuration environment explicitly
    to avoid credential bleed from local files.
    """
    kwargs = {
        "region_name": region_name or getattr(config, "aws_region", "us-east-1")
    }
    
    # Explicitly pass credentials if configured in environment
    if getattr(config, "aws_access_key_id", None) and getattr(config, "aws_secret_access_key", None):
        kwargs["aws_access_key_id"] = config.aws_access_key_id
        kwargs["aws_secret_access_key"] = config.aws_secret_access_key
        
    with _client_lock:
        return boto3.client(service_name, **kwargs)
