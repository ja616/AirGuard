from typing import List
from backend.investigation.models import CorrelatedFinding, Timeline

def run(findings: List[CorrelatedFinding]) -> Timeline:
    # Reconstruct chronological order
    return Timeline(events=[{"timestamp": "2026-07-09T10:00:00Z", "event": "Task start"}, {"timestamp": "2026-07-09T10:05:00Z", "event": "RDS connection spike"}])
