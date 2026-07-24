"""
FastAPI application entrypoint.
"""
import dotenv
dotenv.load_dotenv('.env.local')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1 import investigations, ws, connections, slack_webhooks, health, metrics
from backend.api.v1 import airflow_webhook
from backend.integrations.registry import registry
from backend.integrations.airflow.client import RestAirflowClient
from backend.integrations.aws.registry import AWSRegistryImpl
from backend.integrations.slack.client import RestSlackClient
import logging

def create_app() -> FastAPI:
    app = FastAPI(
        title="AirGuard API",
        description="Agentic Workflow Investigation Copilot for Apache Airflow",
        version="0.1.0",
    )
    
    # Add CORS middleware for the React Dashboard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins for local dev
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include REST routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(metrics.router, prefix="/api/v1")
    app.include_router(connections.router)
    app.include_router(slack_webhooks.router)
    app.include_router(investigations.router, prefix="/api/v1")
    app.include_router(airflow_webhook.router)  # No prefix — router defines its own
    
    from backend.api.v1 import aws_sns_webhook
    app.include_router(aws_sns_webhook.router)

    # Include WebSocket routers
    app.include_router(ws.router, prefix="/api/v1")
        
    @app.on_event("startup")
    def startup_event():
        logger = logging.getLogger(__name__)
        logger.info("Initializing Integration Registry...")
        try:
            registry.register_airflow(RestAirflowClient())
            registry.register_aws(AWSRegistryImpl())
            registry.register_slack(RestSlackClient())
            logger.info("Integration Registry initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Integration Registry: {e}")
        
    return app

app = create_app()
