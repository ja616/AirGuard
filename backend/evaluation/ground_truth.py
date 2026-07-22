from dataclasses import dataclass
from typing import List, Optional

@dataclass
class GroundTruth:
    dag_id: str
    expected_incident_class: str
    expected_root_cause_keywords: List[str]
    expected_confidence_min: float
    expected_confidence_max: float
    expected_artifact_count: int
    is_multi_incident: bool
    secondary_incident_class: Optional[str] = None

EXPECTED_OUTPUTS = [
    GroundTruth(
        dag_id="retry_storm_dag",
        expected_incident_class="INC-EXEC-001",
        expected_root_cause_keywords=["deadlock", "503", "api"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="dependency_failure_dag",
        expected_incident_class="INC-DEP-001",
        expected_root_cause_keywords=["upstream", "code bug"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="unexpected_dag_explosion_dag",
        expected_incident_class="INC-EXEC-002",
        expected_root_cause_keywords=["code bug"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="lambda_failure_dag",
        expected_incident_class="INC-CLD-001",
        expected_root_cause_keywords=["payload", "timeout"],
        expected_confidence_min=0.6,  # Has logs
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="long_running_task_dag",
        expected_incident_class="INC-EXEC-003",
        expected_root_cause_keywords=["hanging", "deadlock"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="scheduler_failure_dag",
        expected_incident_class="INC-SCHED-001",
        expected_root_cause_keywords=["oom", "disconnect"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="schedule_misconfig_dag",
        expected_incident_class="INC-SCHED-002",
        expected_root_cause_keywords=["cron", "config"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="manual_trigger_storm_dag",
        expected_incident_class="INC-OPS-001",
        expected_root_cause_keywords=["panic", "manual"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="backfill_storm_dag",
        expected_incident_class="INC-SCHED-003",
        expected_root_cause_keywords=["catchup"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="resource_contention_dag",
        expected_incident_class="INC-EXEC-004",
        expected_root_cause_keywords=["pool"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="silent_data_failure_dag",
        expected_incident_class="INC-DATA-001",
        expected_root_cause_keywords=["empty"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="partial_recovery_dag",
        expected_incident_class="INC-REC-001",
        expected_root_cause_keywords=["flaky"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="sagemaker_cost_spike_dag",
        expected_incident_class="INC-COST-001",
        expected_root_cause_keywords=["config"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="excessive_parallelism_dag",
        expected_incident_class="INC-OPS-002",
        expected_root_cause_keywords=["expand"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    ),
    GroundTruth(
        dag_id="dag_pause_resume_dag",
        expected_incident_class="INC-OPS-003",
        expected_root_cause_keywords=["accidental", "pause"],
        expected_confidence_min=0.45,
        expected_confidence_max=1.0,
        expected_artifact_count=3,
        is_multi_incident=False
    )
]

def get_ground_truth(dag_id: str) -> Optional[GroundTruth]:
    for gt in EXPECTED_OUTPUTS:
        if gt.dag_id == dag_id:
            return gt
    return None
