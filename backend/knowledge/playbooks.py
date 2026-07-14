"""
Concrete operational playbooks for incident types.
These dictate exactly how the Skills must execute the investigation.
"""
from backend.knowledge.models import OperationalPlaybook, InvestigationQuestion, BlastRadiusRule

RETRY_STORM_PLAYBOOK = OperationalPlaybook(
    incident_id="INC-EXEC-001",
    name="Investigate Retry Storm",
    description="SRE playbook for identifying the root cause of an Airflow retry storm.",
    symptoms=[
        "High Celery queue latency", 
        "Task try_number spiking",
        "Database connection pool exhaustion"
    ],
    required_evidence=[
        "RetryEvidence",
        "CloudTrailEvidence",
        "MetricEvidence"
    ],
    investigation_questions=[
        InvestigationQuestion(
            question="Did retries actually increase above baseline?",
            required_evidence_type="RetryEvidence",
            tool_capability_needed="discovery"
        ),
        InvestigationQuestion(
            question="Was a deployment involved recently?",
            required_evidence_type="CloudTrailEvidence",
            tool_capability_needed="collection"
        ),
        InvestigationQuestion(
            question="Did external APIs throttle or fail?",
            required_evidence_type="MetricEvidence",
            tool_capability_needed="collection"
        )
    ],
    typical_causes=[
        "Database deadlock", 
        "External API rate limits",
        "Bad code deployment"
    ],
    recommended_correlation_strategy="Correlate task failures with deployment timestamps and external API metric spikes.",
    confidence_rules="Add +0.4 for deployment correlation. Add +0.3 for API error spike. Penalty -0.2 if historical baseline matches.",
    recommended_remediation=[
        "Implement exponential backoff", 
        "Rollback recent deployment"
    ],
    blast_radius_rules=[
        BlastRadiusRule(
            dimension="downstream_tasks", 
            expansion_strategy="DAG dependency traversal"
        ),
        BlastRadiusRule(
            dimension="worker_nodes",
            expansion_strategy="Check co-located task latency"
        )
    ],
    future_extensions=[
        "Automated backoff injection"
    ]
)

COST_SPIKE_PLAYBOOK = OperationalPlaybook(
    incident_id="INC-COST-001",
    name="Investigate Cost Spike",
    description="SRE playbook for AWS resource cost anomalies.",
    symptoms=["Billing alert triggered", "Task runtime extended"],
    required_evidence=["CostEvidence", "TaskEvidence"],
    investigation_questions=[
        InvestigationQuestion(
            question="What specific resource type caused the spike?",
            required_evidence_type="CostEvidence",
            tool_capability_needed="discovery"
        ),
        InvestigationQuestion(
            question="Did task duration increase proportionally?",
            required_evidence_type="TaskEvidence",
            tool_capability_needed="collection"
        )
    ],
    typical_causes=["Instance type change", "Data volume spike"],
    recommended_correlation_strategy="Overlap Cost Explorer granularity with Task Execution Window.",
    confidence_rules="Add +0.5 for exact AWS Tag match. Add +0.3 for pure temporal overlap.",
    recommended_remediation=["Revert instance type", "Set max runtime"],
    blast_radius_rules=[
        BlastRadiusRule(dimension="budget_impact", expansion_strategy="Monthly burn rate projection")
    ],
    future_extensions=["Proactive cost estimation"]
)
