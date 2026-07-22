import uuid
from typing import Optional, List
from datetime import datetime, timezone
from backend.domain.investigation import (
    Investigation, 
    InvestigationState, 
    InvestigationMetadata, 
    ArtifactType
)
from backend.infrastructure.repositories.interfaces import IInvestigationRepository

class InvestigationService:
    def __init__(self, repository: IInvestigationRepository):
        self.repository = repository

    def create_investigation(self, started_by: str, airflow_environment: str = "production", aws_account: str = "default") -> Investigation:
        investigation_id = str(uuid.uuid4())
        metadata = InvestigationMetadata(
            started_by=started_by,
            airflow_environment=airflow_environment,
            aws_account=aws_account
        )
        investigation = Investigation(id=investigation_id, metadata=metadata)
        return self.repository.create(investigation)

    def get_investigation(self, investigation_id: str) -> Optional[Investigation]:
        return self.repository.get(investigation_id)

    def list_investigations(self, limit: int = 100, offset: int = 0) -> List[Investigation]:
        return self.repository.list(limit, offset)

    def update_state(self, investigation_id: str, new_state: InvestigationState, progress: int = None) -> Optional[Investigation]:
        investigation = self.repository.get(investigation_id)
        if not investigation:
            return None
            
        investigation.state = new_state
        if progress is not None:
            investigation.progress = progress
        
        # Handle terminal states
        if new_state in [InvestigationState.COMPLETED, InvestigationState.FAILED]:
            investigation.metadata.completed_at = datetime.now(timezone.utc)
            if investigation.metadata.started_at:
                delta = investigation.metadata.completed_at - investigation.metadata.started_at
                investigation.metadata.duration_seconds = int(delta.total_seconds())
                
        return self.repository.update(investigation)

    def add_artifact(self, investigation_id: str, artifact: ArtifactType) -> Optional[Investigation]:
        investigation = self.repository.get(investigation_id)
        if not investigation:
            return None
            
        investigation.artifacts.append(artifact)
        return self.repository.update(investigation)

    def execute_investigation_pipeline_async(self, investigation_id: str, dag_id: str, user_query: str):
        from backend.observability.logger import setup_logger, investigation_id_var, get_trace_id
        
        # Immediately setup logger context for the background thread
        investigation_id_var.set(investigation_id)
        get_trace_id() # Initialize trace ID if empty
        logger = setup_logger(__name__)
        
        try:
            # 1. Assert STARTING before anything else
            self.update_state(investigation_id, InvestigationState.STARTING, progress=5)
            logger.info(f"Starting async pipeline for {investigation_id}")
            
            # 2. Perform all imports and setups inside the protected block
            from backend.agent.agentcore_adapter import AgentCoreAdapter
            from backend.investigation.models import InvestigationRequest
            from backend.integrations.registry import registry
            from backend.infrastructure.redis_pubsub import redis_pubsub
            import time
            
            accumulated_artifacts = []
            
            def state_callback(state: InvestigationState, progress: int, artifacts: Optional[List[ArtifactType]]):
                self.update_state(investigation_id, state, progress=progress)
                if artifacts:
                    accumulated_artifacts.extend(artifacts if isinstance(artifacts, list) else [artifacts])
                time.sleep(1.0)
                from backend.domain.events import StateChangeEvent
                evt = StateChangeEvent(
                    id=f"evt_{uuid.uuid4().hex[:8]}",
                    new_state=state.value,
                    progress=progress or 0
                )
                redis_pubsub.publish(f"investigation:{investigation_id}:state", evt.model_dump(mode='json'))
                
            req = InvestigationRequest.from_legacy(
                investigation_id=investigation_id,
                dag_id=dag_id,
                user_query=user_query,
            )
            
            harness = AgentCoreAdapter()
            report = harness.run_investigation(req, state_callback=state_callback)
            
            # Dispatch Slack Notification (legacy format)
            self.update_state(investigation_id, InvestigationState.SLACK_DISPATCH, progress=95)
            slack = registry.get_slack_client()
            slack.post_message(
                f"✅ *Investigation Completed*\n*DAG:* `{dag_id}`\n*ID:* `{investigation_id}`\n*Root Cause:* {report.root_cause}"
            )
            
            inv = self.repository.get(investigation_id)
            if inv:
                inv.artifacts.extend(accumulated_artifacts)
                self.repository.update(inv)
                
            self.update_state(investigation_id, InvestigationState.COMPLETED, progress=100)
            
        except Exception as e:
            logger.exception(f"Investigation pipeline failed unexpectedly: {e}")
            self.update_state(investigation_id, InvestigationState.FAILED, progress=100)
            from backend.domain.events import StateChangeEvent
            from backend.infrastructure.redis_pubsub import redis_pubsub
            evt = StateChangeEvent(
                id=f"evt_{uuid.uuid4().hex[:8]}",
                new_state=InvestigationState.FAILED.value,
                progress=100
            )
            redis_pubsub.publish(f"investigation:{investigation_id}:state", evt.model_dump(mode='json'))

    def execute_investigation_pipeline_async_context(self, investigation_id: str, incident_context):
        """
        New primary pipeline entry point: accepts a structured IncidentContext.
        Produces richer Slack alerts including severity, environment, and trigger source.
        """
        from backend.observability.logger import setup_logger, investigation_id_var, get_trace_id

        investigation_id_var.set(investigation_id)
        get_trace_id()
        logger = setup_logger(__name__)

        try:
            self.update_state(investigation_id, InvestigationState.STARTING, progress=5)
            logger.info(
                f"Starting context-driven pipeline for {investigation_id} | "
                f"workflow={incident_context.workflow_id} | "
                f"severity={incident_context.severity.value} | "
                f"goal={incident_context.investigation_goal.value}"
            )

            from backend.agent.agentcore_adapter import AgentCoreAdapter
            from backend.investigation.models import InvestigationRequest
            from backend.integrations.registry import registry
            from backend.infrastructure.redis_pubsub import redis_pubsub
            import time

            accumulated_artifacts = []

            def state_callback(state: InvestigationState, progress: int, artifacts: Optional[List[ArtifactType]]):
                self.update_state(investigation_id, state, progress=progress)
                if artifacts:
                    accumulated_artifacts.extend(artifacts if isinstance(artifacts, list) else [artifacts])
                time.sleep(1.0)
                from backend.domain.events import StateChangeEvent
                evt = StateChangeEvent(
                    id=f"evt_{uuid.uuid4().hex[:8]}",
                    new_state=state.value,
                    progress=progress or 0
                )
                redis_pubsub.publish(f"investigation:{investigation_id}:state", evt.model_dump(mode='json'))

            req = InvestigationRequest.from_context(
                investigation_id=investigation_id,
                ctx=incident_context,
            )

            harness = AgentCoreAdapter()
            report = harness.run_investigation(req, state_callback=state_callback)

            # Dispatch enriched Slack alert
            self.update_state(investigation_id, InvestigationState.SLACK_DISPATCH, progress=95)
            slack = registry.get_slack_client()
            sev = incident_context.severity.value.upper()
            env = incident_context.environment
            sev_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(sev, "✅")
            node_info = (
                f"\n*Failed Node:* `{incident_context.failed_node_id}`"
                if incident_context.failed_node_id else ""
            )
            retry_info = (
                f" (attempt {incident_context.retry_number})"
                if incident_context.retry_number else ""
            )
            slack.post_message(
                f"{sev_emoji} *[{sev}/{env}] Investigation Completed*\n"
                f"*Workflow:* `{incident_context.workflow_id}`{node_info}{retry_info}\n"
                f"*Root Cause:* {report.root_cause}\n"
                f"*ID:* `{investigation_id}` | "
                f"Triggered by: {incident_context.trigger_source.value}"
            )

            inv = self.repository.get(investigation_id)
            if inv:
                inv.artifacts.extend(accumulated_artifacts)
                self.repository.update(inv)

            self.update_state(investigation_id, InvestigationState.COMPLETED, progress=100)

        except Exception as e:
            logger.exception(f"Context-driven investigation pipeline failed: {e}")
            self.update_state(investigation_id, InvestigationState.FAILED, progress=100)
            from backend.domain.events import StateChangeEvent
            from backend.infrastructure.redis_pubsub import redis_pubsub
            evt = StateChangeEvent(
                id=f"evt_{uuid.uuid4().hex[:8]}",
                new_state=InvestigationState.FAILED.value,
                progress=100
            )
            redis_pubsub.publish(f"investigation:{investigation_id}:state", evt.model_dump(mode='json'))

