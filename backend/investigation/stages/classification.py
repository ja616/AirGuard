from backend.investigation.models import InvestigationRequest, ClassifiedIncident
from backend.taxonomy.registry import get_incident_definition

def run(request: InvestigationRequest) -> ClassifiedIncident:
    # Deterministic classification based on reported symptom
    # For now, hardcode to RETRY_STORM for testing the pipeline
    definition = get_incident_definition("INC-EXEC-001")
    return ClassifiedIncident(request=request, definition=definition)
