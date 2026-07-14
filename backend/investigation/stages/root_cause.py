from backend.investigation.models import RCAHypothesis, Timeline

def run(timeline: Timeline) -> RCAHypothesis:
    """
    Deterministic root cause extraction for Phase 2.
    Since we don't use LLMs, we extract the earliest anomalous trigger event 
    from the topologically sorted timeline.
    """
    if not timeline.events:
        return RCAHypothesis(root_cause="Unknown")
        
    first_event = timeline.events[0]
    event_type = first_event.get("event_type", "Unknown")
    
    if event_type == "ScheduleEvidence":
        return RCAHypothesis(root_cause="Schedule misconfiguration")
    elif event_type == "CloudTrailEvidence":
        return RCAHypothesis(root_cause="Deployment change")
    else:
        return RCAHypothesis(root_cause=f"Anomaly originating from {event_type}")
