from typing import List
from datetime import datetime
import uuid
from backend.evidence.models import Evidence, TaskEvidence
from backend.evaluation.synthetic_incidents.base_scenario import BaseSyntheticScenario
from backend.evaluation.models import GroundTruth
from backend.core.constants import ConfidenceLevel

class MissingEvidenceScenario(BaseSyntheticScenario):
    @property
    def name(self) -> str:
        return "Missing Evidence"

    @property
    def difficulty(self) -> str:
        return "Medium"

    @property
    def category(self) -> str:
        return "Anomaly"

    @property
    def context(self) -> str:
        return "Legitimate failure but no logs"

    def generate_evidence(self) -> List[Evidence]:
        return [
            TaskEvidence(
                id=str(uuid.uuid4()),
                source="airflow",
                timestamp=datetime.utcnow(),
                reliability=1.0,
                confidence=1.0,
                raw_payload={},
                normalized_payload={},
                dag_id="mock_dag",
                task_id="mock_task",
                execution_date=datetime.utcnow().isoformat(),
                state="failed",
                metadata={}
            )
        ]

    def get_ground_truth(self) -> GroundTruth:
        return GroundTruth(
            expected_root_cause="Anomaly originating from TaskEvidence",
            expected_primary_evidence_types=['TaskEvidence'],
            expected_timeline_length_min=1,
            expected_confidence_level=ConfidenceLevel.HIGH,
            expected_blast_radius_workflows=["mock_dag"]
        )
