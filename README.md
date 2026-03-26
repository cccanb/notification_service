# Notification Service

A standalone microservice that receives notification events from other services and delivers them asynchronously via pluggable channels (email, webhook). The API returns a `task_id` immediately; actual delivery is handled by a Celery worker with automatic retries and a dead-letter queue.

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Task queue | Celery 5 |
| Broker / result backend | Redis 7 |
| Data validation | Pydantic v2 |
| HTTP client (webhook) | httpx |
| Dev SMTP server | MailHog |
| Tests | pytest, unittest.mock, TestClient |
| Containers | Docker Compose |

## Project Structure

```
app/
├── main.py                   # FastAPI app — /healthz + /notify
├── models/
│   ├── email_notification.py    # EmailNotification (Pydantic)
│   ├── webhook_notification.py  # WebhookNotification (Pydantic)
│   └── notification_event.py   # Union type discriminated by "channel"
├── channels/
│   ├── base.py              # BaseChannel — ABC with validate() + abstract send()
│   ├── email.py             # EmailChannel (reads SMTP env vars)
│   └── webhook.py          # WebhookChannel stubimplementation
└── worker/
    ├── celery_app.py        # Celery instance, queue config
    ├── tasks.py             # send_notification + dead_letter_sink tasks
    └── helpers.py           # CHANNEL_REGISTRY, resolve_channel, retry/DLQ helpers
tests/
├── test_api.py              # Endpoint tests (TestClient + mocks)
├── test_models.py           # Pydantic validation tests
└── test_helpers.py          # compute_retry_delay unit tests
```

## API

### `GET /healthz`
```json
200 OK
{"status": "ok"}
```

### `POST /notify`
Send a notification. The `channel` field is the discriminator.

**Email:**
```json
{
  "channel": "email",
  "recipient": "user@example.com",
  "subject": "Hello",
  "body": "Message text",
  "metadata": {}
}
```

**Webhook:**
```json
{
  "channel": "webhook",
  "url": "https://example.com/hook",
  "payload": {"key": "value"},
  "metadata": {"headers": {"X-Custom": "value"}}
}
```

**Response `202 Accepted`:**
```json
{"task_id": "<celery-task-uuid>"}
```

**Response `422`** — validation error (missing fields, bad URL, unknown channel, etc.)

## Configuration

Create a `.env` file before running (not committed to the repo):

```env
REDIS_PORT=6379
MAILHOG_SMTP_PORT=1025
MAILHOG_HTTP_PORT=8025
NOTIFICATION_SERVICE_PORT=8001

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## Running

### Docker Compose (recommended)

```bash
docker-compose up --build
```

Services started:

| Service | Port |
|---|---|
| FastAPI | 8001 |
| Redis | 6379 |
| MailHog SMTP | 1025 |
| MailHog Web UI | 8025 |

### Local Dev

```bash
source venv/bin/activate

# Terminal 1 — API server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 — Celery worker
celery -A app.worker.tasks worker --loglevel=info -Q notifications,notifications.failed
```

Quick manual test:
```bash
curl -X POST http://localhost:8001/notify \
  -H "Content-Type: application/json" \
  -d '{"channel":"email","recipient":"a@b.com","subject":"Hi","body":"Hello"}'
```

## Tests

```bash
pytest
```

| File | What it covers |
|---|---|
| `test_api.py` | `/healthz` response, `/notify` 202 acceptance, 422 on bad input |
| `test_models.py` | Pydantic validation — valid payloads and expected `ValidationError` cases |
| `test_helpers.py` | `compute_retry_delay()` — exponential backoff bounds and non-negativity |

## How It Works

1. `POST /notify` validates the payload, calls `send_notification.apply_async`, returns `task_id`.
2. The Celery worker picks up the task from the `notifications` queue.
3. `helpers.resolve_channel()` looks up the channel class in `CHANNEL_REGISTRY`, calls `validate()` then `send()`.
4. On failure, the task retries with exponential backoff + full jitter (capped).
5. After max retries, the event is forwarded to the `notifications.failed` queue (`dead_letter_sink` task).
