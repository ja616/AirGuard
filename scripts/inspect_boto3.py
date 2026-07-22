import boto3
import inspect

client = boto3.client("bedrock-agentcore", region_name="us-east-1")
import json
print(list(client.meta.service_model.operation_model("InvokeHarness").input_shape.members.keys()))
