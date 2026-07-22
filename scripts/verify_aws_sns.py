import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/aws/sns"

def test_subscription_confirmation():
    print("Testing SNS Subscription Confirmation...")
    payload = {
        "Type": "SubscriptionConfirmation",
        "MessageId": "165545c9-2a5c-472c-8df2-7ff2be2b3b1b",
        "Token": "2336412f37...",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:MyCostAnomalyTopic",
        "Message": "You have chosen to subscribe to the topic...",
        "SubscribeURL": "https://sns.us-east-1.amazonaws.com/?Action=ConfirmSubscription&TopicArn=...",
        "Timestamp": "2026-07-21T12:00:00.000Z",
    }
    
    headers = {"x-amz-sns-message-type": "SubscriptionConfirmation"}
    response = requests.post(BASE_URL, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_cost_anomaly_notification():
    print("Testing Cost Anomaly Notification...")
    
    # Cost anomaly messages are JSON strings inside the 'Message' field
    anomaly_details = {
        "anomalyId": "ca-1234567890",
        "anomalyScore": 0.95,
        "impact": {
            "totalImpact": 1500.50, # Should trigger HIGH severity
            "impactPercentage": 25.5
        },
        "anomalyStartDate": "2026-07-21T00:00:00Z"
    }
    
    payload = {
        "Type": "Notification",
        "MessageId": "857345c9-2a5c-472c-8df2-7ff2be2b3b1b",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:MyCostAnomalyTopic",
        "Message": json.dumps(anomaly_details),
        "Timestamp": "2026-07-21T12:05:00.000Z",
    }
    
    headers = {"x-amz-sns-message-type": "Notification"}
    response = requests.post(BASE_URL, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


if __name__ == "__main__":
    test_subscription_confirmation()
    time.sleep(1)
    test_cost_anomaly_notification()
