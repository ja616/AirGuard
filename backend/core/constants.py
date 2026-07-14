from enum import Enum
from typing import Set

class SupportedAWSService(str, Enum):
    CLOUDWATCH = "cloudwatch"
    CLOUDTRAIL = "cloudtrail"
    SAGEMAKER = "sagemaker"
    LAMBDA = "lambda"
    S3 = "s3"
    COST_EXPLORER = "cost_explorer"

class IncidentCategory(str, Enum):
    SCHEDULING = "scheduling"
    EXECUTION = "execution"
    DEPENDENCY = "dependency"
    PERFORMANCE = "performance"
    INFRASTRUCTURE = "infrastructure"
    COST = "cost"
    DATA = "data"
    COMPOSITE = "composite"

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

UNSUPPORTED_BOUNDARIES: Set[str] = {
    "ec2_debugging",
    "networking",
    "vpc",
    "kubernetes",
    "application_code_debugging",
    "generic_aws_troubleshooting",
    "multi_cloud",
    "predictive_ai",
    "self_healing"
}

class SystemPrinciples(str, Enum):
    FACTS_BEFORE_AI = "Facts before AI"
    DETERMINISTIC_BEFORE_PROBABILISTIC = "Deterministic before probabilistic"
    NO_AUTONOMOUS_REMEDIATION = "No autonomous remediation"
