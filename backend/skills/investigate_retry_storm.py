from typing import List
from backend.skills.base import BaseSkill
from backend.knowledge.models import OperationalPlaybook
from backend.knowledge.playbooks import RETRY_STORM_PLAYBOOK
from backend.evidence.models import Evidence
from backend.investigation.models import InvestigationRequest, OperationalReport
from backend.investigation.pipeline import DeterministicInvestigationEngine

class InvestigateRetryStormSkill(BaseSkill):
    def __init__(self):
        self.engine = DeterministicInvestigationEngine()
        self._playbook = RETRY_STORM_PLAYBOOK

    @property
    def playbook(self) -> OperationalPlaybook:
        return self._playbook

    def execute(self, request: InvestigationRequest, evidence: List[Evidence]) -> OperationalReport:
        if not self.validate_evidence(evidence):
            missing = self.missing_evidence_requirements(evidence)
            raise ValueError(f"Investigation blocked. Missing evidence for {self.playbook.name}:\n" + "\n".join(missing))
            
        # In a fully integrated phase 2, the evidence would be passed directly into the correlation engine.
        return self.engine.execute(request)
