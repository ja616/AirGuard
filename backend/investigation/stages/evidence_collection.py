from typing import List
from backend.investigation.models import ClassifiedIncident, CollectedEvidence

def run(classified: ClassifiedIncident) -> List[CollectedEvidence]:
    # Deterministic evidence collection
    # In Phase 2, this will call the Tool Layer
    return [
        CollectedEvidence(source="airflow_db", raw_data={"task_tries": 6}),
        CollectedEvidence(source="cloudwatch", raw_data={"cpu_utilization": 95.0})
    ]
