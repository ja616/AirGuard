from backend.integrations.core.interfaces import IAirflowClient, IAWSRegistry, ISlackClient

class IntegrationRegistry:
    """
    Central factory and registry for all external integrations.
    Provides dependency injection for the investigation engine.
    """
    def __init__(self):
        self._airflow_client: IAirflowClient = None
        self._aws_registry: IAWSRegistry = None
        self._slack_client: ISlackClient = None

    def register_airflow(self, client: IAirflowClient):
        self._airflow_client = client

    def register_aws(self, registry: IAWSRegistry):
        self._aws_registry = registry

    def register_slack(self, client: ISlackClient):
        self._slack_client = client

    def get_airflow_client(self) -> IAirflowClient:
        if not self._airflow_client:
            raise NotImplementedError("Airflow client has not been registered.")
        return self._airflow_client

    def get_aws_registry(self) -> IAWSRegistry:
        if not self._aws_registry:
            raise NotImplementedError("AWS Registry has not been registered.")
        return self._aws_registry

    def get_slack_client(self) -> ISlackClient:
        if not self._slack_client:
            raise NotImplementedError("Slack client has not been registered.")
        return self._slack_client

# Global integration registry instance
registry = IntegrationRegistry()
