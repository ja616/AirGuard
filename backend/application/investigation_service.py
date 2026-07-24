"""
InvestigationService — AirGuard Application Layer
===================================================
Owns the investigation lifecycle:
  create → run pipeline → persist artifacts → notify → complete

Responsibilities:
  - CRUD on Investigation domain objects via IInvestigationRepository
  - Launching and tracking the background pipeline (state machine)
  - Publishing Redis state-change events for WebSocket consumers
  - Dispatching Slack notifications (content built in integrations/slack/blocks.py)

NOT responsible for:
  - Slack message formatting (→ integrations/slack/blocks.py)
  - Evidence collection (→ tools/registry.py via AgentCoreAdapter)
  - Deterministic reasoning (→ investigation/pipeline.py)
  - Nova LLM polish (→ investigation/stages/nova_formatter.py)
"""
import uuid
from typing import Optional, List
from datetime import datetime, timezone

from backend.domain.investigation import (
    Investigation,
    InvestigationState,
    InvestigationMetadata,
    ArtifactType,
)
from backend.infrastructure.repositories.interfaces import IInvestigationRepository


class InvestigationService:
    def __init__(self, repository: IInvestigationRepository):
        self.repository = repository

    # ─────────────────────────────────────────────────────────────────────────
    # CRUD
    # ─────────────────────────────────────────────────────────────────────────

    def create_investigation(
        self,
        started_by: str,
        airflow_environment: str = "production",
        aws_account: str = "default",
    ) -> Investigation:
        investigation_id = str(uuid.uuid4())
        metadata = InvestigationMetadata(
            started_by=started_by,
            airflow_environment=airflow_environment,
            aws_account=aws_account,
        )
        investigation = Investigation(id=investigation_id, metadata=metadata)
        return self.repository.create(investigation)

    def get_investigation(self, investigation_id: str) -> Optional[Investigation]:
        return self.repository.get(investigation_id)

    def list_investigations(self, limit: int = 100, offset: int = 0) -> List[Investigation]:
        return self.repository.list(limit, offset)

    def update_state(
        self,
        investigation_id: str,
        new_state: InvestigationState,
        progress: int = None,
    ) -> Optional[Investigation]:
        investigation = self.repository.get(investigation_id)
        if not investigation:
            return None

        investigation.state = new_state
        if progress is not None:
            investigation.progress = progress

        if new_state in [InvestigationState.COMPLETED, InvestigationState.FAILED]:
            investigation.metadata.completed_at = datetime.now(timezone.utc)
            if investigation.metadata.started_at:
                delta = (
                    investigation.metadata.completed_at
                    - investigation.metadata.started_at
                )
                investigation.metadata.duration_seconds = int(delta.total_seconds())

        return self.repository.update(investigation)

    def add_artifact(
        self, investigation_id: str, artifact: ArtifactType
    ) -> Optional[Investigation]:
        investigation = self.repository.get(investigation_id)
        if not investigation:
            return None
        investigation.artifacts.append(artifact)
        return self.repository.update(investigation)

    # ─────────────────────────────────────────────────────────────────────────
    # Public pipeline entry points
    # ─────────────────────────────────────────────────────────────────────────

    def execute_investigation_pipeline_async(
        self, investigation_id: str, dag_id: str, user_query: str
    ):
        """Legacy entry point: accepts a free-text query string."""
        from backend.investigation.models import InvestigationRequest

        req = InvestigationRequest.from_legacy(
            investigation_id=investigation_id,
            dag_id=dag_id,
            user_query=user_query,
        )
        self._run_pipeline(investigation_id, req, incident_context=None)

    def execute_investigation_pipeline_async_context(
        self, investigation_id: str, incident_context
    ):
        """Primary entry point: accepts a structured IncidentContext."""
        from backend.investigation.models import InvestigationRequest

        req = InvestigationRequest.from_context(
            investigation_id=investigation_id,
            ctx=incident_context,
        )
        self._run_pipeline(investigation_id, req, incident_context=incident_context)

    # ─────────────────────────────────────────────────────────────────────────
    # Shared pipeline state machine (private)
    # ─────────────────────────────────────────────────────────────────────────

    def _run_pipeline(self, investigation_id: str, req, incident_context=None):
        """
        Single shared state machine for all investigation runs.
        Handles: STARTING → evidence collection → reasoning → SLACK_DISPATCH → COMPLETED.
        Catches all exceptions and marks the investigation FAILED on error.
        """
        from backend.observability.logger import (
            setup_logger, investigation_id_var, get_trace_id,
        )
        from backend.agent.agentcore_adapter import AgentCoreAdapter
        from backend.integrations.registry import registry
        from backend.integrations.slack.blocks import format_investigation_complete
        from backend.infrastructure.redis_pubsub import redis_pubsub
        from backend.domain.events import StateChangeEvent
        import time

        investigation_id_var.set(investigation_id)
        get_trace_id()
        logger = setup_logger(__name__)

        accumulated_artifacts: List[ArtifactType] = []

        def _state_callback(
            state: InvestigationState,
            progress: int,
            artifacts: Optional[List[ArtifactType]],
        ):
            self.update_state(investigation_id, state, progress=progress)
            if artifacts:
                accumulated_artifacts.extend(
                    artifacts if isinstance(artifacts, list) else [artifacts]
                )
            time.sleep(1.0)
            evt = StateChangeEvent(
                id=f"evt_{uuid.uuid4().hex[:8]}",
                new_state=state.value,
                progress=progress or 0,
            )
            redis_pubsub.publish(
                f"investigation:{investigation_id}:state",
                evt.model_dump(mode="json"),
            )

        def _publish_failed():
            evt = StateChangeEvent(
                id=f"evt_{uuid.uuid4().hex[:8]}",
                new_state=InvestigationState.FAILED.value,
                progress=100,
            )
            redis_pubsub.publish(
                f"investigation:{investigation_id}:state",
                evt.model_dump(mode="json"),
            )

        try:
            self.update_state(investigation_id, InvestigationState.STARTING, progress=5)
            logger.info(
                f"Starting pipeline for investigation={investigation_id} "
                f"dag={req.dag_id} "
                + (
                    f"severity={incident_context.severity.value} "
                    f"goal={incident_context.investigation_goal.value}"
                    if incident_context else ""
                )
            )

            harness = AgentCoreAdapter()
            report = harness.run_investigation(req, state_callback=_state_callback)

            # ── Slack notification (content built in integrations/slack/blocks) ──
            self.update_state(
                investigation_id, InvestigationState.SLACK_DISPATCH, progress=95
            )
            slack = registry.get_slack_client()
            message = format_investigation_complete(
                report=report,
                investigation_id=investigation_id,
                context=incident_context,
            )
            slack.post_message(message)

            # ── Persist artifacts ─────────────────────────────────────────────
            inv = self.repository.get(investigation_id)
            if inv:
                inv.artifacts.extend(accumulated_artifacts)
                self.repository.update(inv)

            self.update_state(
                investigation_id, InvestigationState.COMPLETED, progress=100
            )

        except Exception as exc:
            logger.exception(f"Investigation pipeline failed: {exc}")
            self.update_state(investigation_id, InvestigationState.FAILED, progress=100)
            _publish_failed()
