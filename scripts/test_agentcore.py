import os
import sys

# Setup mock environment
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AGENTCORE_HARNESS_ID"] = "arn:aws:bedrock-agentcore:us-east-1:069089526426:harness/harness_tdsyz-XMmJkdl9mS"
os.environ["AIRGUARD_ENV"] = "local"
sys.path.append(os.path.abspath("."))

from backend.agent.agentcore_adapter import AgentCoreAdapter
from backend.investigation.models import InvestigationRequest
from datetime import datetime, timezone

def test():
    adapter = AgentCoreAdapter()
    req = InvestigationRequest(
        investigation_id="97f0ae50-6f4e-4131-a5a9-d7278519a278",
        dag_id="test_dag",
        execution_date=datetime.now(timezone.utc).isoformat(),
        reported_symptom="test symptom",
        environment="production"
    )
    
    try:
        res = adapter._run_inline_tool_loop(os.environ["AGENTCORE_HARNESS_ID"], ["get_dag_runs"], req)
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
