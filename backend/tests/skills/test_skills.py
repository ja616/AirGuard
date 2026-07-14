import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.skills.investigate_retry_storm import InvestigateRetryStormSkill
from backend.investigation.models import InvestigationRequest

def test_retry_storm_skill():
    skill = InvestigateRetryStormSkill()
    assert "INC-EXEC-001" in skill.supported_incidents()
    assert "get_worker_logs" in skill.required_tools()
    
    request = InvestigationRequest(
        dag_id="dag1",
        task_id="task1",
        execution_date="2026-07-09T00:00:00Z",
        reported_symptom="latency"
    )
    assert skill.validate(request) is True
    
    # execute will currently use the deterministic dummy engine
    result = skill.execute(request)
    assert result.classified_incident.definition.id == "INC-EXEC-001"
