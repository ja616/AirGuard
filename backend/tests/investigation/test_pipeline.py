import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.investigation.models import InvestigationRequest
from backend.investigation.pipeline import DeterministicInvestigationEngine
from backend.core.constants import ConfidenceLevel

def test_pipeline_execution():
    engine = DeterministicInvestigationEngine()
    request = InvestigationRequest(
        dag_id="test_dag",
        task_id="test_task",
        execution_date="2026-07-09T00:00:00Z",
        reported_symptom="task failed rapidly"
    )
    
    result = engine.execute(request)
    
    # Verify strict output contract
    assert result.request.dag_id == "test_dag"
    assert result.classified_incident.definition.id == "INC-EXEC-001"
    assert len(result.evidence) == 2
    assert result.rca.root_cause is not None
    assert result.confidence.level == ConfidenceLevel.HIGH
    assert len(result.recommendations) == 2
