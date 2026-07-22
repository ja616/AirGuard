from typing import List, Any
from backend.investigation.models import CorrelatedFinding, Timeline

def run(evidence: List[Any], findings: List[CorrelatedFinding]) -> Timeline:
    events = []
    
    for ev in evidence:
        ts = ev.timestamp.isoformat() if hasattr(ev.timestamp, "isoformat") else str(ev.timestamp)
        events.append({
            "timestamp": ts,
            "event": f"Evidence collected from source: {ev.source}"
        })
        
    for f in findings:
        # Give findings a timestamp slightly after evidence collection
        if evidence:
            ts = evidence[-1].timestamp
            ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        else:
            ts_str = "2026-07-09T10:05:00Z"
            
        events.append({
            "timestamp": ts_str,
            "event": f"Correlation Engine: {f.finding}"
        })
        
    # Sort chronologically
    events.sort(key=lambda x: x["timestamp"])
    
    if not events:
        events.append({"timestamp": "2026-07-09T10:00:00Z", "event": "Investigation started but no events recorded."})
        
    return Timeline(events=events)
