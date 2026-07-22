import boto3
import os
import json

client = boto3.client("bedrock-agentcore", region_name="us-east-1")
harness_id = "arn:aws:bedrock-agentcore:us-east-1:069089526426:harness/harness_tdsyz-XMmJkdl9mS"
tools = [{
    "type": "inline_function",
    "name": "get_dag_runs",
    "config": {
        "inlineFunction": {
            "description": "Retrieve DAG runs",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    }
}]

messages = [{"role": "user", "content": [{"text": "Call the get_dag_runs tool."}]}]

try:
    response = client.invoke_harness(
        harnessArn=harness_id,
        runtimeSessionId="test-session",
        messages=messages,
        tools=tools
    )
    for event in response.get("stream", []):
        print("EVENT:", event)
except Exception as e:
    print("ERROR:", e)
