# AirGuard Demo Scenarios

We've pre-loaded Airflow with specific scenarios to demonstrate AirGuard's cross-domain reasoning. You can trigger them using our local simulation scripts.

## Scenario A: The Phantom Retraining Storm (Cost Spike)

**The Problem:** A routine daily ML training pipeline suddenly causes an unexpected AWS cost spike. Nothing appears broken in Airflow (the DAG succeeds, tasks complete, no Airflow alerts), and there are no explicitly failed SageMaker jobs. Yet the AWS bill increases dramatically.

*   **The Setup:** A misconfigured DAG (`ml_training_pipeline`) is running successfully every minute instead of daily, spawning hundreds of costly SageMaker jobs. No Airflow alerts are triggered because tasks are technically succeeding.
*   **The Trigger:** Simulate an AWS Cost Explorer anomaly alert by running:
    ```bash
    python scripts/trigger_aws_anomaly.py
    ```
*   **The Magic:** AirGuard correlates the AWS cost spike with the excessive Airflow backfill runs, catching the silent failure that a human operator would miss if they only looked at the green Airflow dashboard.

## Scenario B: SageMaker Timeout Loop

**The Problem:** The daily ML Pipeline is stuck. Everything works until the `Train SageMaker Model` task. Instead of completing normally, the SageMaker training job times out after 30 minutes, Airflow automatically retries the task 3 times, and every retry launches a new SageMaker training job. Downstream tasks never execute, leaving the DAG in a long-running state.

*   **The Setup:** The `daily_ml_pipeline` DAG is stuck in a loop. The SageMaker API times out, and Airflow retries 3 times, leaving orphaned jobs consuming resources in AWS.
*   **The Trigger:** Fire an Airflow Webhook payload by running:
    ```bash
    python scripts/trigger_investigation.py
    ```
    *(Note: Ensure Block #6 is uncommented in the script)*
*   **The Magic:** AirGuard reads the Airflow task logs for the "timeout" keyword, detects the high `try_number`, and correlates this to diagnose a Rapid Retry Storm + Timeout Anomaly. It immediately recommends manual intervention to kill the orphaned jobs in AWS and correct the Airflow timeout configuration.
