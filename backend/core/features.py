"""
Feature flags acting as strict architecture constraints.
"""

class FeatureFlags:
    # Phase 1: Deterministic Engine Only
    AGENTCORE_ENABLED: bool = False
    LLM_EXPLANATION_ENABLED: bool = False
    
    # Strict Architecture Constraints
    AUTONOMOUS_REMEDIATION_ENABLED: bool = False

features = FeatureFlags()
