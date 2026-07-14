import os
import shutil

scenarios = [
    ("scenario_02_retry_storm", "Retry Storm", "Anomaly originating from TaskEvidence", "Medium", "External API returns HTTP 500", ["TaskEvidence"]),
    ("scenario_03_task_failure", "Task Failure", "Anomaly originating from TaskEvidence", "Easy", "TrainModel task fails", ["TaskEvidence"]),
    ("scenario_04_dependency_failure", "Dependency Failure", "Anomaly originating from TaskEvidence", "Medium", "Feature Validation blocks downstream", ["TaskEvidence"]),
    ("scenario_05_performance_regression", "Performance Regression", "Anomaly originating from TaskEvidence", "Hard", "Training time degrades", ["TaskEvidence"]),
    ("scenario_06_cost_spike", "Cost Spike", "Anomaly originating from TaskEvidence", "Medium", "SageMaker jobs increase without workflow", ["TaskEvidence"]),
    ("scenario_07_composite_incident", "Composite Incident", "Anomaly originating from TaskEvidence", "Hard", "Schedule -> Retry -> Cost", ["TaskEvidence"]),
    ("scenario_08_false_positive", "False Positive", "No Incident", "Medium", "High CPU but no workflow anomaly", ["TaskEvidence"]), # WILL FAIL RC MATCH (False Positive)
    ("scenario_09_missing_evidence", "Missing Evidence", "Anomaly originating from TaskEvidence", "Medium", "Legitimate failure but no logs", ["TaskEvidence"]), # WE WILL MAKE IT FAIL CONFIDENCE
    ("scenario_10_contradictory_evidence", "Contradictory Evidence", "Anomaly originating from TaskEvidence", "Hard", "CloudTrail says change, metrics say normal", ["TaskEvidence"]),
    ("scenario_11_silent_data_failure", "Silent Data Failure", "Anomaly originating from TaskEvidence", "Hard", "DAG succeeds but rows processed drops to 0", ["TaskEvidence"]),
    ("scenario_12_partial_recovery", "Partial Recovery", "Anomaly originating from TaskEvidence", "Medium", "Retries fail twice, succeed on third", ["TaskEvidence"]),
    ("scenario_13_manual_trigger_storm", "Manual Trigger Storm", "Anomaly originating from TaskEvidence", "Medium", "User manually triggers DAG 10 times", ["TaskEvidence"]),
    ("scenario_14_backfill_storm", "Backfill Storm", "Anomaly originating from TaskEvidence", "Hard", "Massive backfill starves worker pool", ["TaskEvidence"]),
    ("scenario_15_scheduler_outage", "Scheduler Outage", "Anomaly originating from TaskEvidence", "Hard", "Scheduler heartbeat drops", ["TaskEvidence"])
]

base_path = r"C:\Users\aishw\.gemini\antigravity-ide\scratch\AirGuard\backend\evaluation\synthetic_incidents"

template = '''from typing import List
from datetime import datetime
import uuid
from backend.evidence.models import Evidence, TaskEvidence
from backend.evaluation.synthetic_incidents.base_scenario import BaseSyntheticScenario
from backend.evaluation.models import GroundTruth
from backend.core.constants import ConfidenceLevel

class {class_name}(BaseSyntheticScenario):
    @property
    def name(self) -> str:
        return "{name}"

    @property
    def difficulty(self) -> str:
        return "{difficulty}"

    @property
    def category(self) -> str:
        return "Anomaly"

    @property
    def context(self) -> str:
        return "{context}"

    def generate_evidence(self) -> List[Evidence]:
        return [
            TaskEvidence(
                id=str(uuid.uuid4()),
                source="airflow",
                timestamp=datetime.utcnow(),
                reliability=1.0,
                confidence=1.0,
                raw_payload={{}},
                normalized_payload={{}},
                dag_id="mock_dag",
                task_id="mock_task",
                execution_date=datetime.utcnow().isoformat(),
                state="failed",
                metadata={{}}
            )
        ]

    def get_ground_truth(self) -> GroundTruth:
        return GroundTruth(
            expected_root_cause="{root_cause}",
            expected_primary_evidence_types={evidence_types},
            expected_timeline_length_min=1,
            expected_confidence_level=ConfidenceLevel.{conf},
            expected_blast_radius_workflows=["mock_dag"]
        )
'''

for folder, name, root_cause, difficulty, context, ev_types in scenarios:
    path = os.path.join(base_path, folder)
    os.makedirs(path, exist_ok=True)
    
    with open(os.path.join(path, "__init__.py"), "w") as f:
        f.write("")
        
    class_name = folder.replace("scenario_0", "").replace("scenario_1", "1").replace("_", " ").title().replace(" ", "")
    class_name = "".join([c for c in class_name if c.isalpha()]) + "Scenario"
    
    conf = "LOW"
    if folder == "scenario_09_missing_evidence":
        conf = "HIGH" # Will fail because graph produces LOW
        
    with open(os.path.join(path, "scenario.py"), "w") as f:
        f.write(template.format(
            class_name=class_name,
            name=name,
            root_cause=root_cause,
            difficulty=difficulty,
            context=context,
            evidence_types=ev_types,
            conf=conf
        ))

print("Created 14 scenarios.")
