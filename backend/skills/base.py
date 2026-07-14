"""
Base Skill abstraction. Skills are now true Investigation Workflows.
They consume playbooks from the Knowledge Base to guide their execution.
"""
from abc import ABC, abstractmethod
from typing import List
from backend.knowledge.models import OperationalPlaybook
from backend.evidence.models import Evidence
from backend.investigation.models import InvestigationRequest, InvestigationResult

class BaseSkill(ABC):
    """
    A Skill is a complete operational investigation playbook execution.
    It guarantees that all engineering questions are answered before 
    allowing the LLM or Correlation Engine to proceed.
    """
    
    @property
    @abstractmethod
    def playbook(self) -> OperationalPlaybook:
        """The Knowledge Base playbook this skill executes."""
        pass
        
    def validate_evidence(self, collected_evidence: List[Evidence]) -> bool:
        """
        Verify that all mandatory engineering questions defined in the playbook
        have their required evidence types present before correlation begins.
        """
        evidence_types = {e.__class__.__name__ for e in collected_evidence}
        for question in self.playbook.investigation_questions:
            if question.required_evidence_type not in evidence_types:
                return False
        return True
        
    def missing_evidence_requirements(self, collected_evidence: List[Evidence]) -> List[str]:
        """
        Returns exactly which questions cannot be answered yet.
        """
        evidence_types = {e.__class__.__name__ for e in collected_evidence}
        missing = []
        for question in self.playbook.investigation_questions:
            if question.required_evidence_type not in evidence_types:
                missing.append(
                    f"Cannot answer '{question.question}' - missing {question.required_evidence_type}"
                )
        return missing

    @abstractmethod
    def execute(self, request: InvestigationRequest, evidence: List[Evidence]) -> InvestigationResult:
        """Execute the pipeline, armed with the verified domain evidence."""
        pass
