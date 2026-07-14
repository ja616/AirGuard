import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.core.constants import SupportedAWSService, IncidentCategory, UNSUPPORTED_BOUNDARIES, SystemPrinciples
from backend.core.features import features

def test_supported_aws_services():
    assert SupportedAWSService.S3 == "s3"
    assert len(SupportedAWSService) == 6

def test_unsupported_boundaries():
    assert "kubernetes" in UNSUPPORTED_BOUNDARIES
    assert "vpc" in UNSUPPORTED_BOUNDARIES

def test_feature_flags_enforce_phase1():
    assert features.AGENTCORE_ENABLED is False
    assert features.LLM_EXPLANATION_ENABLED is False
    assert features.AUTONOMOUS_REMEDIATION_ENABLED is False

def test_system_principles():
    assert SystemPrinciples.NO_AUTONOMOUS_REMEDIATION == "No autonomous remediation"
