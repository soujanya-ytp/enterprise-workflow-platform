# Enterprise Workflow & Operations Platform

Configurable service requests, multi-step approvals, role-based access, comments, audit history, escalation and operational dashboards.

## Included modules

- Create service requests with category and priority
Route requests through multi-step approval chains
Enforce role-based approval and prevent invalid state transitions
Persist comments and audit events
Filter and paginate request listings
Report status counts and overdue approvals

## Architecture

- FastAPI REST API with OpenAPI docs
- SQLAlchemy relational persistence and database models
- Bearer-token authentication and role checks
- Domain-focused endpoints and business workflows
- Pytest smoke/authorization tests
- Dockerfile and Docker Compose configuration
- Stack-independent acceptance criteria and scoring rubric

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export APP_SECRET="use-a-long-random-secret"
uvicorn app.main:app --reload --port 8101
```

API docs: http://127.0.0.1:8101/docs
Health check: http://127.0.0.1:8101/health

## Run tests

```bash
pytest -q
```

## Docker

```bash
docker compose up --build
```

## Evaluation use

Use `docs/acceptance-criteria.md` to build independent black-box tests and `docs/evaluation-rubric.md` for consistent stack-independent scoring. Add a real frontend, migration tooling, richer test fixtures, concurrency tests, and a production identity provider before treating this as a production system.

## Scope note

This is a complex backend benchmark starter with interactive OpenAPI documentation, not a complete production-ready full-stack product. Authentication is a self-contained demonstration implementation; replace it with a vetted identity provider for production.
