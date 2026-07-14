import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.tools.discovery import list_recent_runs
from backend.tools.evidence import get_task_logs
from backend.tools.decorators import deterministic_tool

def test_list_recent_runs():
    runs = list_recent_runs(dag_id="test_dag", limit=2)
    assert len(runs) == 2
    assert runs[0].dag_id == "test_dag"

def test_get_task_logs():
    log = get_task_logs(dag_id="test_dag", task_id="test_task", execution_date="2026-07-09")
    assert log.error_count == 5
    assert "ERROR" in log.content

def test_decorator_retry_logic():
    # Helper to test decorator retry tracking
    attempts = 0
    
    @deterministic_tool(timeout=1, retries=2)
    def flaky_tool():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ValueError("Simulated network failure")
        return "Success"
        
    result = flaky_tool()
    assert result == "Success"
    assert attempts == 2
