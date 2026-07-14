import unittest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

class TestE2EScenarios(unittest.TestCase):

    def test_environment_validation_endpoint(self):
        """Validates Module 1: Pre-flight checks for all integrations"""
        response = client.get("/api/v1/connections")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("integrations", data)

    def test_observability_metrics_endpoint(self):
        """Validates Module 6: Prometheus Metrics exposure"""
        # Trigger an endpoint to generate some metrics
        client.get("/api/v1/connections")
        response = client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("airguard_", response.text)

    def test_slack_interactive_webhook(self):
        """Validates Module 5: Slack Block Kit Interactive callbacks"""
        # We need to register a stub Slack client to avoid 500
        from backend.integrations.registry import registry
        from backend.integrations.slack.client import RestSlackClient
        if not registry.has_slack_client():
            registry.register_slack_client(RestSlackClient())
            
        payload = {
            "payload": '{"type": "block_actions", "user": {"username": "e2e_tester"}, "actions": [{"action_id": "approve_123", "value": "inv_123"}]}'
        }
        response = client.post("/api/v1/slack/events", data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_start_investigation_pipeline(self):
        """Validates Module 4: Triggering the core pipeline via API"""
        payload = {
            "dag_id": "retry_storm_dag",
            "user_query": "Why did the retry storm dag fail?"
        }
        response = client.post("/api/v1/investigations", json=payload)
        self.assertIn(response.status_code, (200, 202))

if __name__ == '__main__':
    unittest.main()
