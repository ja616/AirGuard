import boto3
import os

client = boto3.client(
    "bedrock-agentcore",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)
harness_arn = os.environ.get("AGENTCORE_HARNESS_ID", "arn:aws:bedrock-agentcore:us-east-1:111122223333:harness/harness_tdsyz-XMmJkdl9mS")
try:
    response = client.invoke_harness(
        harnessArn=harness_arn,
        runtimeSessionId="test-123",
        messages=[{"role": "user", "content": [{"text": "Hello"}]}],
        tools=[]
    )
    print("KEYS:", response.keys())
    print("RESPONSE:", response)
except Exception as e:
    print("ERROR:", e)
