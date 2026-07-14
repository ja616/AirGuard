from typing import List
from backend.skills.base import BaseSkill
from backend.knowledge.models import OperationalPlaybook
from backend.knowledge.playbooks import COST_SPIKE_PLAYBOOK
from backend.evidence.models import Evidence
from backend.investigation.models import InvestigationRequest, InvestigationResult
from backend.investigation.pipeline import DeterministicInvestigationEngine

class InvestigateCostSpikeSkill(BaseSkill):
    def __init__(self):
        self.engine = DeterministicInvestigationEngine()
        self._playbook = COST_SPIKE_PLAYBOOK

    @property
    def playbook(self) -> OperationalPlaybook:
        return self._playbook

    def execute(self, request: InvestigationRequest, evidence: List[Evidence]) -> InvestigationResult:
        if not self.validate_evidence(evidence):
            missing = self.missing_evidence_requirements(evidence)
            raise ValueError(f"Investigation blocked. Missing evidence for {self.playbook.name}:\n" + "\n".join(missing))
            
        return self.engine.execute(request)
