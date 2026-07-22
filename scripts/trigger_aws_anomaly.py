import requests
import json
import uuid

# The endpoint for AWS SNS webhooks in AirGuard
SNS_ENDPOINT = "http://localhost:8000/api/v1/aws/sns"

def trigger_cost_anomaly():
    """
    Simulates AWS Cost Explorer sending an SNS Notification to AirGuard.
    This is exactly what the payload looks like in production.
    """
    anomaly_id = str(uuid.uuid4())[:8]
    
    # 1. The inner Cost Anomaly JSON that AWS generates
    cost_anomaly_message = {
        "anomalyId": f"ca-{anomaly_id}",
        "anomalyStartDate": "2026-07-22T00:00:00Z",
        "impact": {
            "totalImpact": 4200.50, # A $4,200 spike!
            "totalImpactPercentage": 450.0
        },
        "dimension": "SERVICE",
        "dimensionValue": "AWS SageMaker",
        "description": "Unexpected spike in AWS SageMaker usage detected."
    }

    # 2. The outer SNS Notification wrapper
    sns_payload = {
        "Type": "Notification",
        "MessageId": str(uuid.uuid4()),
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:CostAnomalyAlerts",
        "Subject": "AWS Cost Anomaly Detected",
        "Message": json.dumps(cost_anomaly_message), # SNS sends the message as a stringified JSON
        "Timestamp": "2026-07-22T10:00:00.000Z"
    }

    print(f"\n🚨 Simulating AWS Cost Anomaly SNS Trigger...")
    print(f"   Payload: {json.dumps(cost_anomaly_message, indent=2)}")
    
    # Send the HTTP POST request (Simulating AWS SNS calling our Webhook)
    headers = {"x-amz-sns-message-type": "Notification"}
    response = requests.post(SNS_ENDPOINT, json=sns_payload, headers=headers)
    
    print(f"\n✅ Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    print("\n👉 Now check the AirGuard Command Center!")

if __name__ == "__main__":
    trigger_cost_anomaly()
