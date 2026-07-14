"""
Skill Selector Planner.
Maps natural language intent strictly to predefined, immutable sequences of Skills.
"""
from typing import List

class SkillPlanner:
    """
    Decides which rigid sequence of deterministic skills should execute based on intent.
    The LLM never invents the execution order; the Planner explicitly orchestrates it.
    """
    
    # Pre-defined deterministic sequences
    SKILL_SEQUENCES = {
        "cost_spike": [
            "InvestigateCostSpike",
            "GenerateTimeline",
            "GenerateRCA",
            "GenerateExecutiveSummary"
        ],
        "retry_storm": [
            "InvestigateRetryStorm",
            "GenerateTimeline",
            "GenerateRCA",
            "GenerateExecutiveSummary"
        ],
        "task_failure": [
            "InvestigateTaskFailure",
            "GenerateTimeline",
            "GenerateRCA",
            "GenerateExecutiveSummary"
        ],
        "dependency": [
            "InvestigateDependencyFailure",
            "GenerateTimeline",
            "GenerateRCA",
            "GenerateExecutiveSummary"
        ],
        "schedule": [
            "InvestigateScheduleChange",
            "GenerateTimeline",
            "GenerateRCA",
            "GenerateExecutiveSummary"
        ],
        "default": [
            "GenerateTimeline",
            "GenerateRCA",
            "GenerateExecutiveSummary"
        ]
    }
    
    def select_skills(self, user_query: str) -> List[str]:
        """
        Maps a natural language query to a sequence of rigid skills.
        In a full implementation, this uses a fast LLM intent classifier.
        For deterministic guarantees, we map the intent to the hardcoded DAG list.
        """
        query_lower = user_query.lower()
        
        if "cost" in query_lower or "spend" in query_lower:
            return self.SKILL_SEQUENCES["cost_spike"]
        elif "retry" in query_lower or "storm" in query_lower:
            return self.SKILL_SEQUENCES["retry_storm"]
        elif "dependency" in query_lower or "block" in query_lower:
            return self.SKILL_SEQUENCES["dependency"]
        elif "schedule" in query_lower or "cron" in query_lower:
            return self.SKILL_SEQUENCES["schedule"]
        elif "fail" in query_lower or "error" in query_lower:
            return self.SKILL_SEQUENCES["task_failure"]
        else:
            return self.SKILL_SEQUENCES["default"]
