# AirGuard — Agentic Workflow Investigation Copilot

> **Automatically investigates Apache Airflow pipeline failures using a hybrid LLM + deterministic reasoning architecture.**
> When a DAG task fails, AirGuard collects evidence from Airflow, AWS CloudWatch, CloudTrail, and Cost Explorer, then deterministically synthesizes a root cause and dispatches a rich Slack report — without hallucinating.

---

## Architecture

```
Airflow on_failure_callback
        │  POST /api/v1/airflow/webhook
        ▼
  IncidentContext          ← normalized, Airflow-agnostic
        │
        ▼
  Capability Planner       ← scores & selects evidence capabilities by severity
        │
        ▼
  AgentCore Harness        ← LLM-directed tool loop (evidence collection only)
        │  (falls back to direct execution when AGENTCORE_HARNESS_ID not set)
        ▼
  Evidence Bundle          ← strongly-typed, normalized payloads
        │
        ▼
  Deterministic Engine     ← pure Python reasoning, no LLM, no hallucinations
    stages: normalize → classify → correlate → timeline → rca → confidence → recs
        │
        ▼
  Nova Formatter (optional) ← LLM polish of human-facing fields only
        │
        ▼
  Operational Report       → Slack Block Kit + Frontend Dashboard
```

**The Detective vs. Judge pattern:**  
The LLM (AgentCore) is the Detective — it collects evidence but never draws conclusions.  
The Deterministic Engine is the Judge — it reasons from normalized boolean signals, never raw text.

---

## Quick Start (local demo, ~5 minutes)

### Prerequisites
- Docker Desktop (running)
- Node.js 18+
- Python 3.11+

### 1. Clone and configure
```bash
git clone https://github.com/your-org/AirGuard.git
cd AirGuard

# Create your local environment file
cp .env.local.example .env.local
# Edit .env.local — add your AWS credentials if you want Nova polish + CloudWatch
# Everything works without AWS credentials (deterministic engine runs offline)
```

### 2. Start all services
```bash
docker compose up -d --build
```
Wait ~45 seconds for Airflow to initialize. Check readiness:
```bash
curl http://localhost:8080/health   # Airflow webserver
curl http://localhost:8000/api/v1/health  # AirGuard backend
```

### 3. Launch the dashboard
```bash
cd frontend && npm install && npm run dev
# Open http://localhost:3000
```

### 4. Trigger a demo investigation

**Option A — Automatic (webhook, recommended):**  
Manually trigger the SageMaker pipeline in Airflow UI at http://localhost:8080.  
When `train_sagemaker_model` fails, the DAG's `on_failure_callback` automatically POSTs to AirGuard.  
Watch the investigation appear live on http://localhost:3000.

**Option B — Manual trigger script:**
```bash
python scripts/trigger_investigation.py
```
Then open http://localhost:3000/investigations and click the new investigation.

---

## Demo Scenarios

### Scenario A: SageMaker Timeout Loop (`daily_ml_pipeline`)
The `train_sagemaker_model` task times out after 30 minutes and retries 3 times, each retry spawning a new orphaned SageMaker job in AWS. AirGuard detects the Timeout Loop pattern from task logs, correlates the retry count, and recommends killing the orphaned jobs.

### Scenario B: ETL Retry Storm (`data_pipeline_etl`)
The `extract_raw_data` task fails repeatedly due to a database connection timeout, triggering a retry storm. AirGuard classifies it as an isolated task failure with no cascade correlation.

---

## Webhook Integration (production use)

AirGuard exposes `POST /api/v1/airflow/webhook` for Airflow callbacks.  
Your DAGs call it automatically via `dags/airguard_callbacks.py`:

```python
from airguard_callbacks import notify_airguard_failure, notify_airguard_retry

default_args = {
    ...
    'on_failure_callback': notify_airguard_failure,
    'on_retry_callback':   notify_airguard_retry,
}
```

Authentication: `X-AirGuard-Token` header (set `AIRGUARD_WEBHOOK_TOKEN` in `.env.local`).  
For production, point `AIRGUARD_URL` in `airguard_callbacks.py` to your deployed backend.

---

## Project Structure

```
backend/
  api/v1/              ← FastAPI routes (thin controllers)
    airflow_webhook.py   ← webhook endpoint (auth + normalize + dispatch)
    investigations.py    ← investigation CRUD + manual trigger
  application/
    investigation_service.py  ← lifecycle state machine
  agent/
    agentcore_adapter.py      ← bridges planner ↔ AgentCore harness
    planner/selector.py       ← capability scoring & tool selection
    executor.py               ← parallel tool execution
  investigation/
    pipeline.py               ← deterministic stage orchestrator
    stages/
      normalization.py         ← evidence → signals dict
      classification.py        ← signals → incident type
      correlation.py           ← findings from graph + signals
      root_cause.py            ← RCA hypothesis
      confidence.py            ← confidence score
      recommendations.py       ← action list
      nova_formatter.py        ← (optional) LLM polish
  tools/
    registry.py               ← atomic evidence collection tools
    schemas.py                ← tool descriptions (single source of truth)
  integrations/
    airflow/
      client.py               ← Airflow REST API adapter
      incident_adapter.py     ← Airflow payload → IncidentContext
    slack/
      client.py               ← Slack API adapter
      blocks.py               ← all Slack message formatting
    aws/                      ← CloudWatch, CloudTrail, Cost Explorer clients
dags/
  airguard_callbacks.py       ← shared on_failure/on_retry callbacks
  daily_ml_pipeline.py        ← SageMaker Timeout Loop scenario
  data_pipeline_etl.py        ← ETL Retry Storm scenario
frontend/                     ← Next.js dashboard
```

---

## Development

```bash
# Run backend tests
pytest backend/tests/ -v

# Format
black backend/

# Rebuild backend after code changes
docker compose up -d --build airguard-backend
```

---

## Environment Variables

See [.env.local.example](.env.local.example) for all variables with documentation.  
The only **required** variable for full local demo is none — everything has safe defaults.  
AWS credentials unlock: Nova LLM polish, CloudWatch Lambda metrics, CloudTrail audit logs.
