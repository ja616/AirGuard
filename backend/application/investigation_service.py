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
            from backend.investigation.pipeline import DeterministicInvestigationEngine
            from backend.investigation.models import InvestigationRequest
            from backend.integrations.registry import registry
            import time
            
            # Artifacts generated during the pipeline run will be accumulated here
            # and only appended to the investigation if the pipeline completely succeeds.
            accumulated_artifacts = []
            
            def state_callback(state: InvestigationState, progress: int, artifacts: Optional[List[ArtifactType]]):
                self.update_state(investigation_id, state, progress=progress)
                if artifacts:
                    # Depending on how the engine pushes artifacts, we either append them to the local list,
                    # or in the case of COMPLETED, they are final.
                    # Since our modified engine pushes all of them at COMPLETED, we just use them there.
                    accumulated_artifacts.extend(artifacts if isinstance(artifacts, list) else [artifacts])
                    
                # Add artificial delay to simulate real work for observation
                time.sleep(1.0)
                
            req = InvestigationRequest(
                dag_id=dag_id,
                execution_date=datetime.now(timezone.utc).isoformat(),
                reported_symptom=user_query
            )
            
            engine = DeterministicInvestigationEngine()
            report = engine.execute(req, state_callback=state_callback)
            
            # Dispatch Slack Notification
            self.update_state(investigation_id, InvestigationState.SLACK_DISPATCH, progress=95)
            slack = registry.get_slack_client()
            slack.post_message(
                f"✅ *Investigation Completed*\n*DAG:* `{dag_id}`\n*ID:* `{investigation_id}`\n*Root Cause:* {report.root_cause}"
            )
            
            # Commit the artifacts since we succeeded
            inv = self.repository.get(investigation_id)
            if inv:
                inv.artifacts.extend(accumulated_artifacts)
                self.repository.update(inv)
                
            # Finish up
            self.update_state(investigation_id, InvestigationState.COMPLETED, progress=100)
            
        except Exception as e:
            logger.exception(f"Investigation pipeline failed unexpectedly: {e}")
            self.update_state(investigation_id, InvestigationState.FAILED, progress=100)
