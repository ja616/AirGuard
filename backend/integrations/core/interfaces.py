from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IIntegrationClient(ABC):
    @abstractmethod
    def health(self) -> bool:
        """Returns True if the integration is healthy and reachable."""
        pass

    @abstractmethod
    def ping(self) -> float:
        """Returns the latency in milliseconds."""
        pass

    @abstractmethod
    def capabilities(self) -> List[str]:
        """Returns a list of supported capability strings."""
        pass


class IAirflowClient(IIntegrationClient):
    @abstractmethod
    def get_health(self) -> Dict[str, Any]: pass
    
    @abstractmethod
    def get_version(self) -> str: pass
    
    @abstractmethod
    def get_scheduler_state(self) -> str: pass
    
    @abstractmethod
    def get_dag_runs(self, dag_id: str) -> List[Dict[str, Any]]: pass
    
    @abstractmethod
    def get_task_instances(self, dag_id: str, run_id: str) -> List[Dict[str, Any]]: pass
    
    @abstractmethod
    def get_task_logs(self, dag_id: str, run_id: str, task_id: str, try_number: int = 1) -> str: pass

    @abstractmethod
    def get_dag_graph(self, dag_id: str) -> Dict[str, Any]: pass

    @abstractmethod
    def get_read_only_metadata(self) -> Dict[str, Any]: pass
    
    @abstractmethod
    def trigger_dag_run(self, dag_id: str) -> str: pass
    
    @abstractmethod
    def get_dag_run_by_id(self, dag_id: str, run_id: str) -> Dict[str, Any]: pass
    
    @abstractmethod
    def get_all_dag_ids(self) -> List[str]: pass
    
    @abstractmethod
    def get_task_xcoms(self, dag_id: str, run_id: str, task_id: str) -> List[Dict[str, Any]]: pass
    
    @abstractmethod
    def get_pool_stats(self) -> Dict[str, Any]: pass


class ISlackClient(IIntegrationClient):
    @abstractmethod
    def post_message(self, text: str, channel: str = None) -> Dict[str, Any]: pass

    @abstractmethod
    def create_thread(self, text: str, channel: str = None) -> Dict[str, Any]: pass

    @abstractmethod
    def reply_in_thread(self, text: str, thread_ts: str, channel: str = None) -> Dict[str, Any]: pass

    @abstractmethod
    def send_report_blocks(self, blocks: List[Dict[str, Any]], channel: str = None) -> Dict[str, Any]: pass

    @abstractmethod
    def send_approval_blocks(self, blocks: List[Dict[str, Any]], channel: str = None) -> Dict[str, Any]: pass


# AWS Specific Service Interfaces
class ICloudWatchClient(IIntegrationClient):
    @abstractmethod
    def get_metric_data(self, queries: List[Dict[str, Any]], start_time: Any, end_time: Any) -> Dict[str, Any]: pass
    
    @abstractmethod
    def get_lambda_errors(self, function_name: str, start_time: Any, end_time: Any) -> int: pass
    
    @abstractmethod
    def get_lambda_duration(self, function_name: str, start_time: Any, end_time: Any) -> float: pass
    
    @abstractmethod
    def get_sagemaker_training_metrics(self, job_name: str, start_time: Any, end_time: Any) -> Dict[str, Any]: pass
class ICloudTrailClient(IIntegrationClient): pass
class ICostExplorerClient(IIntegrationClient): pass
class ISageMakerClient(IIntegrationClient): pass
class ILambdaClient(IIntegrationClient): pass

class IS3Client(IIntegrationClient):
    @abstractmethod
    def get_prefix_metrics(self, bucket: str, prefix: str) -> Dict[str, Any]: pass

class IAWSRegistry(ABC):
    @abstractmethod
    def get_cloudwatch_client(self) -> ICloudWatchClient: pass
    
    @abstractmethod
    def get_cloudtrail_client(self) -> ICloudTrailClient: pass
    
    @abstractmethod
    def get_cost_explorer_client(self) -> ICostExplorerClient: pass
    
    @abstractmethod
    def get_sagemaker_client(self) -> ISageMakerClient: pass
    
    @abstractmethod
    def get_lambda_client(self) -> ILambdaClient: pass

    @abstractmethod
    def get_s3_client(self) -> IS3Client: pass
