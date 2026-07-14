import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.taxonomy.models import IncidentDefinition, SeverityLevel
from backend.core.constants import IncidentCategory
from backend.taxonomy.registry import get_incident_definition, RETRY_STORM_INCIDENT

def test_incident_definition_validation():
    # Valid definition
    inc = IncidentDefinition(
        id="TEST-001",
        name="Test",
        description="A test",
        severity=SeverityLevel.LOW,
        category=IncidentCategory.DATA,
        observable_symptoms=["A"],
        required_evidence=["B"],
        required_tools=["C"],
        correlation_strategy="D",
        confidence_strategy="E",
        possible_root_causes=["F"],
        recommended_remediation=["G"],
        business_impact="H",
        false_positives=["I"],
        future_extensions=["J"]
    )
    assert inc.id == "TEST-001"
    assert inc.supported is True

def test_registry_retrieval():
    inc = get_incident_definition("INC-EXEC-001")
    assert inc.name == "Task Retry Storm"
    assert inc.category == IncidentCategory.EXECUTION

def test_registry_not_found():
    with pytest.raises(ValueError):
        get_incident_definition("UNKNOWN")
