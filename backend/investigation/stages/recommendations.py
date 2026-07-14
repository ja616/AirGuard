from typing import List
from backend.investigation.models import RCAHypothesis, RecommendedAction

def run(rca: RCAHypothesis) -> List[RecommendedAction]:
    # Rule-based recommendations
    return [
        RecommendedAction(action="Increase RDS max connections"),
        RecommendedAction(action="Implement exponential backoff in task")
    ]
