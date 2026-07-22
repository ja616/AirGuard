from typing import List, Dict, Any
from backend.agent.planner.investigation_plan import InvestigationPlan

def run(plan: InvestigationPlan, evidence: List[Any]) -> Dict[str, str]:
    """
    Validates collected evidence against the investigation plan's estimated tools.
    Returns a dictionary mapping tool names to checkmarks.
    """
    validation_report = {}
    
    collected_sources = set(e.source for e in evidence)
    
    # Simple prefix matching for now, as tool names might not exactly match evidence sources
    def is_collected(tool: str) -> bool:
        for source in collected_sources:
            if tool in source or source in tool or tool.replace("get_", "") in source:
                return True
        return False
        
    for tool_name in plan.estimated_tools:
        # User requested specific formatting like CloudWatch returned? ✓
        friendly_name = tool_name.replace("get_", "").replace("_", " ").title()
        status = "✓" if is_collected(tool_name) else "✗"
        validation_report[f"{friendly_name} returned?"] = status
        
    return validation_report
