import json
import os
from typing import Optional
from backend.domain.investigation import Investigation

REPLAY_DIR = os.getenv("AIRGUARD_REPLAY_DIR", "./replays")

def persist_for_replay(investigation: Investigation):
    """
    Persists the complete state of an Investigation (Timeline, Evidence, 
    Operational Report, Status) to disk. This allows the deterministic 
    engine to replay and analyze historical incidents without re-querying 
    Airflow, AWS, or Slack APIs.
    """
    os.makedirs(REPLAY_DIR, exist_ok=True)
    file_path = os.path.join(REPLAY_DIR, f"{investigation.id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(investigation.model_dump_json(indent=2))
        
def load_replay(investigation_id: str) -> Optional[Investigation]:
    """
    Loads a persisted Investigation to enable offline Operational Replay.
    """
    file_path = os.path.join(REPLAY_DIR, f"{investigation_id}.json")
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return Investigation.model_validate(data)
