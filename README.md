# Business Process Automation

An API-first business workflow service that turns incoming customer enquiries and uploaded documents into classified, routed, trackable workflow runs.

## What it does

- Accepts enquiries through a webhook-style REST endpoint.
- Extracts text from PDF, TXT, Markdown and CSV uploads.
- Classifies enquiries into billing, technical, sales, support or general categories.
- Flags urgent requests and routes them to a priority queue.
- Optionally posts completed workflow events to a configurable downstream webhook (including n8n webhook URLs).
- Persists run status, step outputs, timestamps and errors for audit and troubleshooting.

The baseline classifier is deterministic and works without an AI API key. This makes local development and tests reproducible. It is intentionally a rules-based baseline, not a claim of LLM-powered classification. An LLM adapter can be added behind the classifier interface when a deployment needs model-based extraction.

## Architecture

```text
Webhook / Document Upload
          |
          v
   FastAPI API Layer
          |
          v
   Workflow Orchestrator
     |       |        |
     v       v        v
 Extract  Classify   Route
     |       |        |
     +-------+--------+
             |
             v
      Optional Webhook
             |
             v
   Persisted Workflow Run
```

## Run locally

Requires Python 3.11+.

```bash
git clone https://github.com/truly-vivek/ai-business-process-automation.git
cd ai-business-process-automation
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open the interactive API docs at http://127.0.0.1:8000/docs.

## Example: submit an enquiry

```bash
curl -X POST http://127.0.0.1:8000/webhooks/enquiry \
  -H "Content-Type: application/json" \
  -d '{"message":"URGENT: I cannot access my account; please help","customer_name":"Alex","email":"alex@example.com"}'
```

The response includes the run ID, status, category, priority, summary and each workflow step.

## Process a document

Use the `POST /documents/process` endpoint with multipart form data. Supported formats: PDF (text-based PDFs), TXT, MD and CSV. Scanned PDFs without an embedded text layer are not OCR-processed by this version.

## Inspect runs

- `GET /health` — service health
- `POST /webhooks/enquiry` — submit and execute an enquiry workflow
- `POST /documents/process` — extract and process an uploaded document
- `GET /runs` — list recent workflow runs
- `GET /runs/{run_id}` — inspect one run and its execution trace

## Configure downstream automation

Set `NOTIFICATION_WEBHOOK_URL` in `.env` to an endpoint that accepts JSON POST requests. This can be an n8n webhook or another integration endpoint. If unset, the notification step is recorded as skipped and the workflow still completes.

## Run tests

```bash
pytest -q
```

## Configuration

See `.env.example`. SQLite is used by default for a simple local setup. Set `DATABASE_URL` to a SQLAlchemy-compatible database URL for another environment.

## Current scope and limitations

- Workflow execution is synchronous in the API request; a production deployment should move long-running jobs to a queue/worker.
- The default classifier uses transparent keyword rules, not an LLM.
- PDF extraction reads embedded text only; scanned-document OCR is not included.
- Webhook delivery is a single attempt; production use should add retries, signing, idempotency and delivery monitoring.
- Add authentication, authorization, rate limits, retention controls and secret management before exposing this service publicly.

## License

MIT
