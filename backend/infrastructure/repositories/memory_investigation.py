from typing import Optional, List, Dict
import copy
from backend.domain.investigation import Investigation
from backend.infrastructure.repositories.interfaces import IInvestigationRepository

class MemoryInvestigationRepository(IInvestigationRepository):
    def __init__(self):
        self._store: Dict[str, Investigation] = {}

    def create(self, investigation: Investigation) -> Investigation:
        inv_copy = copy.deepcopy(investigation)
        self._store[inv_copy.id] = inv_copy
        return copy.deepcopy(inv_copy)

    def get(self, investigation_id: str) -> Optional[Investigation]:
        inv = self._store.get(investigation_id)
        return copy.deepcopy(inv) if inv else None

    def update(self, investigation: Investigation) -> Investigation:
        inv_copy = copy.deepcopy(investigation)
        self._store[inv_copy.id] = inv_copy
        return copy.deepcopy(inv_copy)

    def list(self, limit: int = 100, offset: int = 0) -> List[Investigation]:
        items = list(self._store.values())
        return [copy.deepcopy(inv) for inv in items[offset : offset + limit]]
