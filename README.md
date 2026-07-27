# agentic-demo-service

A small FastAPI task service used as the **target repository** for the agentic
SDLC platform demonstration. It is intentionally simple but real: it has routes,
models, an in-memory store, a test suite, and a Jenkins pipeline, so the platform
has genuine context to retrieve and a green baseline to verify against.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/tasks` | List all tasks |
| `POST` | `/tasks` | Create a task |
| `GET` | `/tasks/{task_id}` | Get a task by id |

## Run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API.

## Test, lint, and scan

```bash
ruff check .
pytest -q
bandit -r app
```

## Demo seams

This repository is seeded with two deliberate gaps that the agentic platform
closes as part of the demonstration. The baseline is fully green; neither gap is
covered by an existing test.

- **AGENTDEV-1 — add status filtering to `GET /tasks`.**
  `GET /tasks` accepts no `?status=` query parameter yet.
- **AGENTDEV-2 — duplicate id should return 409, not 500.**
  `POST /tasks` raises `DuplicateTaskError` on a repeated id, which is not handled
  and currently surfaces as HTTP 500.
