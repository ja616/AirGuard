from backend.integrations.core.interfaces import IAWSRegistry, ICloudWatchClient, ICloudTrailClient, ICostExplorerClient, ISageMakerClient, ILambdaClient, IS3Client
from backend.integrations.aws.cloudwatch.client import Boto3CloudWatchClient
from backend.integrations.aws.cloudtrail.client import Boto3CloudTrailClient

class AWSRegistryImpl(IAWSRegistry):
    """
    Service-specific client registry for AWS.
    Ensures each service is instantiated with its own strict interface.
    """
    def __init__(self):
        self._cloudwatch = Boto3CloudWatchClient()
        self._cloudtrail = Boto3CloudTrailClient()

    def get_cloudwatch_client(self) -> ICloudWatchClient:
        return self._cloudwatch
        
    def get_cloudtrail_client(self) -> ICloudTrailClient:
        return self._cloudtrail
        
    def get_cost_explorer_client(self) -> ICostExplorerClient:
        raise NotImplementedError("Cost Explorer integration pending.")
        
    def get_sagemaker_client(self) -> ISageMakerClient:
        raise NotImplementedError("SageMaker integration pending.")
        
    def get_lambda_client(self) -> ILambdaClient:
        raise NotImplementedError("Lambda integration pending.")

    def get_s3_client(self) -> IS3Client:
        raise NotImplementedError("S3 integration pending.")
