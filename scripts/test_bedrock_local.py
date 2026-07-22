import boto3
import os
from dotenv import load_dotenv

load_dotenv(".env.local")

client = boto3.client("bedrock-agentcore", region_name=os.getenv("AWS_REGION"))
harness_id = os.getenv("AGENTCORE_HARNESS_ID")
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
    print(f"Invoking {harness_id}...")
    response = client.invoke_harness(
        harnessArn=harness_id,
        runtimeSessionId="00000000-0000-0000-0000-000000000000",
        model={"bedrockModelConfig": {"modelId": "us.amazon.nova-pro-v1:0"}},
        messages=messages,
        tools=tools
    )
    for event in response.get("stream", []):
        print("EVENT:", event)
except Exception as e:
    print("ERROR:", e)
