import time
import requests
from typing import Dict, Any, List
from backend.integrations.core.interfaces import IAirflowClient
from backend.integrations.core.retry import with_retry, IntegrationException
from backend.integrations.core.telemetry import with_telemetry
from backend.integrations.core.config import config

class RestAirflowClient(IAirflowClient):
    def __init__(self):
        self.base_url = config.airflow_api_url
        self.auth = (config.airflow_username, config.airflow_password)

    @with_retry(max_retries=3, initial_backoff=1.0)
    @with_telemetry("Airflow", "health")
    def health(self) -> bool:
        response = requests.get(f"{self.base_url}/health", auth=self.auth, timeout=5)
        response.raise_for_status()
        return response.json().get("metadatabase", {}).get("status") == "healthy"

    @with_telemetry("Airflow", "ping")
    def ping(self) -> float:
        start = time.time()
        self.health()
        return (time.time() - start) * 1000

    def capabilities(self) -> List[str]:
        return ["dag_runs", "task_instances", "logs", "graph", "metadata"]

    @with_retry(max_retries=3)
    @with_telemetry("Airflow", "get_health")
    def get_health(self) -> Dict[str, Any]:
        return requests.get(f"{self.base_url}/health", auth=self.auth, timeout=5).json()

    @with_retry(max_retries=3)
    @with_telemetry("Airflow", "get_version")
    def get_version(self) -> str:
        response = requests.get(f"{self.base_url}/version", auth=self.auth, timeout=5)
        return response.json().get("version", "unknown")

    @with_retry(max_retries=3)
    @with_telemetry("Airflow", "get_scheduler_state")
    def get_scheduler_state(self) -> str:
        health_data = self.get_health()
        return health_data.get("scheduler", {}).get("status", "unknown")

    @with_retry(max_retries=3)
    @with_telemetry("Airflow", "get_dag_runs")
    def get_dag_runs(self, dag_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/dags/{dag_id}/dagRuns"
        response = requests.get(url, auth=self.auth, timeout=10)
        response.raise_for_status()
        return response.json().get("dag_runs", [])

    @with_retry(max_retries=3)
    @with_telemetry("Airflow", "get_task_instances")
    def get_task_instances(self, dag_id: str, run_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/dags/{dag_id}/dagRuns/{run_id}/taskInstances"
        response = requests.get(url, auth=self.auth, timeout=10)
        response.raise_for_status()
        return response.json().get("task_instances", [])

    @with_retry(max_retries=3)
    @with_telemetry("Airflow", "get_task_logs")
    def get_task_logs(self, dag_id: str, run_id: str, task_id: str, try_number: int = 1) -> str:
        url = f"{self.base_url}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/logs/{try_number}"
        response = requests.get(url, auth=self.auth, timeout=10)
        response.raise_for_status()
        return response.text

    @with_retry(max_retries=3)
    @with_telemetry("Airflow", "get_dag_graph")
    def get_dag_graph(self, dag_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/dags/{dag_id}/details"
        response = requests.get(url, auth=self.auth, timeout=10)
        response.raise_for_status()
        return response.json()

    @with_retry(max_retries=3)
    @with_telemetry("Airflow", "get_read_only_metadata")
    def get_read_only_metadata(self) -> Dict[str, Any]:
        url = f"{self.base_url}/config"
        response = requests.get(url, auth=self.auth, headers={"Accept": "application/json"}, timeout=10)
        return response.json() if response.ok else {}
