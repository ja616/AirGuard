# AirGuard

**AirGuard** is an Agentic Workflow Investigation Copilot designed to autonomously investigate pipeline failures, correlate telemetry across Apache Airflow and AWS, and dispatch real-time operational reports to Slack. 

Built using a deterministic pipeline engine, AirGuard eliminates hallucinations while providing high-quality, reproducible root cause analysis.

## Features
- **Deterministic Investigation Pipeline**: Granular state machine (`Queued` → `CollectingEvidence` → `NormalizingEvidence` → `Correlating` → `GeneratingTimeline` → `GeneratingReport` → `Completed`) tracking the full lifecycle of an incident.
- **Deep Integrations**: Natively connects with Apache Airflow REST APIs, AWS CloudWatch Metrics, and Slack Webhooks.
- **Background Orchestration**: Uses FastAPI BackgroundTasks to reliably queue and process investigations without blocking the API. Guaranteed persistent tracking even if individual tasks fail.
- **Comprehensive Observability**: Exposes `/api/v1/health` and `/api/v1/metrics` endpoints. Correlates all logs back to an `investigation_id` and `trace_id`.

## Architecture
- **API**: FastAPI (Python 3.11+)
- **Persistence**: In-Memory Repository (with strict transaction boundaries to emulate ACID properties)
- **Engine**: A staged pipeline architecture (Classification → Collection → Normalization → Correlation → RCA → Recommendations).
- **Deployment**: Fully containerized with `docker-compose`, spanning local Airflow instances, Redis, Postgres, and the AirGuard backend.

## Quick Start

### 1. Requirements
- Docker and Docker Compose
- Python 3.11+
- AWS Credentials (optionally configured)

### 2. Environment Variables
Create a `.env.local` file in the root directory:
```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```

### 3. Run with Docker Compose
```bash
docker compose up -d --build
```
This will spin up:
- Apache Airflow (Webserver, Scheduler, Postgres DB)
- AirGuard Backend (FastAPI on Port `8000`)
- Redis

### 4. Verify Pipeline
Use the provided script to ensure the orchestration engine is healthy and actively handling investigations:
```bash
python scripts/verify_pipeline.py
```

## Development
- **Run Tests**: `pytest backend/tests/ -v`
- **Formatting**: `black backend/`

## Phase Status
Currently running **Phase 6.1**: Backend Production Hardening.
- Complete `try...except` safety around all background pipelines.
- Persistent artifact and state management.
- Hardened unit tests and integration tests spanning Airflow/AWS integration points.
