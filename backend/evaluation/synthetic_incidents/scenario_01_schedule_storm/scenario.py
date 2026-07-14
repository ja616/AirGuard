"""
Synthetic Scenario 1: Schedule Storm
A junior dev accidentally changes a nightly cron to run every 5 minutes.
"""
from typing import List
from datetime import datetime, timedelta
import uuid

from backend.evidence.models import Evidence, ScheduleEvidence, TaskEvidence, CostEvidence, MetricEvidence
from backend.evaluation.synthetic_incidents.base_scenario import BaseSyntheticScenario
from backend.evaluation.models import GroundTruth
from backend.core.constants import ConfidenceLevel

class ScheduleStormScenario(BaseSyntheticScenario):
    @property
    def name(self) -> str:
        return "Schedule Storm"

    @property
    def difficulty(self) -> str:
        return "Medium"

    @property
    def category(self) -> str:
        return "Cost Anomaly"

    @property
    def context(self) -> str:
        return "Nightly SageMaker Retraining DAG cron accidentally changed from '0 1 * * *' to '*/5 * * * *'"

    def generate_evidence(self) -> List[Evidence]:
        pool = []
        base_time = datetime(2026, 7, 9, 9, 58, 0)
        
        # 1. Trigger: CloudTrail Schedule Changed
        pool.append(
            ScheduleEvidence(
                id=str(uuid.uuid4()),
                source="cloudtrail",
                timestamp=base_time,
                reliability=1.0,
                confidence=1.0,
                raw_payload={"event": "UpdateSchedule", "user": "junior_dev"},
                normalized_payload={},
                metadata={"dag_id": "nightly_retraining"},
                previous_schedule="0 1 * * *",
                new_schedule="*/5 * * * *"
            )
        )
        
        # 2. Symptoms: 5 runs in 20 minutes
        for i in range(5):
            run_time = base_time + timedelta(minutes=2 + (i*5)) # 10:00, 10:05, 10:10...
            job_arn = f"arn:aws:sagemaker:us-east-1:123:training-job/train_{i}"
            
            pool.append(
                TaskEvidence(
                    id=str(uuid.uuid4()),
                    source="airflow_db",
                    timestamp=run_time,
                    reliability=1.0,
                    confidence=1.0,
                    raw_payload={},
                    normalized_payload={},
                    dag_id="nightly_retraining",
                    task_id="train_model",
                    execution_date=run_time.isoformat(),
                    state="success",
                    metadata={"aws_resource_arn": job_arn}
                )
            )
            
            # 3. Impact: Cost observations map to these ARNs
            pool.append(
                CostEvidence(
                    id=str(uuid.uuid4()),
                    source="aws_cost_explorer",
                    timestamp=run_time + timedelta(minutes=1),
                    reliability=1.0,
                    confidence=1.0,
                    raw_payload={},
                    normalized_payload={},
                    granularity="HOURLY",
                    amount=50.0,
                    currency="USD",
                    metadata={"aws_resource_arn": job_arn}
                )
            )
            
        return pool

    def get_ground_truth(self) -> GroundTruth:
        return GroundTruth(
            expected_root_cause="Schedule misconfiguration",
            expected_primary_evidence_types=["ScheduleEvidence", "TaskEvidence", "CostEvidence"],
            expected_timeline_length_min=10, # 1 trigger + 5 tasks + 5 costs
            expected_confidence_level=ConfidenceLevel.HIGH,
            expected_blast_radius_workflows=["nightly_retraining"]
        )
