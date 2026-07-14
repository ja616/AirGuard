import unittest
from backend.integrations.airflow.mappers import map_task_instance_to_evidence
from backend.integrations.aws.mappers import map_cloudwatch_to_evidence, map_cloudtrail_to_evidence
from backend.integrations.slack.mappers import map_slack_response_to_evidence

class TestIntegrationMappers(unittest.TestCase):

    def test_airflow_mapper(self):
        raw_ti = {"dag_id": "test_dag", "dag_run_id": "run_1", "task_id": "t1", "state": "failed"}
        evidence = map_task_instance_to_evidence(raw_ti, "error log here")
        
        self.assertEqual(evidence.dag_id, "test_dag")
        self.assertEqual(evidence.state, "failed")
        self.assertEqual(evidence.log_preview, "error log here")
        self.assertEqual(evidence.type, "airflow_task")

    def test_cloudwatch_mapper(self):
        raw_cw = {
            "MetricDataResults": [
                {
                    "Timestamps": ["2026-07-13T12:00:00Z", "2026-07-13T12:01:00Z"],
                    "Values": [10.5, 12.0]
                }
            ]
        }
        evidence = map_cloudwatch_to_evidence("CPUUtilization", raw_cw)
        
        self.assertEqual(evidence.metric_name, "CPUUtilization")
        self.assertEqual(len(evidence.datapoints), 2)
        self.assertEqual(evidence.datapoints[0]["value"], 10.5)

    def test_cloudtrail_mapper(self):
        raw_ct = {"EventName": "ConsoleLogin", "Username": "alice"}
        evidence = map_cloudtrail_to_evidence(raw_ct)
        
        self.assertEqual(evidence.event_name, "ConsoleLogin")
        self.assertEqual(evidence.username, "alice")

    def test_slack_mapper(self):
        raw_slack = {"channel": "C12345", "ts": "123456789.001"}
        evidence = map_slack_response_to_evidence(raw_slack)
        
        self.assertEqual(evidence.channel, "C12345")
        self.assertEqual(evidence.ts, "123456789.001")

if __name__ == "__main__":
    unittest.main()
