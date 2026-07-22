import boto3
import json

client = boto3.client("bedrock-agentcore", region_name="us-east-1")
model_shape = client.meta.service_model.operation_model("InvokeHarness").input_shape.members["model"]
print(model_shape.members["bedrockModelConfig"].members.keys())
