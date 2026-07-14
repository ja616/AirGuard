"""
Chronological Timeline Reconstruction.
"""
from typing import List
from backend.correlation.models import InvestigationGraph, Timeline, TimelineEvent

class TimelineBuilder:
    """
    Deterministically extracts and sorts all events from the Evidence Graph 
    to reconstruct the exact sequence of events.
    """
    @staticmethod
    def build_timeline(graph: InvestigationGraph) -> Timeline:
        events = []
        
        # Extract all evidence nodes as timeline events
        for node_id, node in graph.nodes.items():
            ev = node.evidence
            
            # Create a human readable description based on the evidence type
            class_name = ev.__class__.__name__
            desc = f"Evidence ({class_name}) captured from {ev.source}."
            if hasattr(ev, 'metric_name'):
                desc = f"Metric spike: {getattr(ev, 'metric_name')} = {getattr(ev, 'value')}"
            elif hasattr(ev, 'state'):
                desc = f"Task/Workflow entered state: {getattr(ev, 'state')}"
                
            events.append(
                TimelineEvent(
                    timestamp=ev.timestamp,
                    event_type=class_name,
                    description=desc,
                    related_node_ids=[node_id]
                )
            )
        
        # Sort chronologically by timestamp
        events.sort(key=lambda x: x.timestamp)
        return Timeline(events=events)
