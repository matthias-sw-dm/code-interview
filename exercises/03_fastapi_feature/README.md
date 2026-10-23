# 03 - FastAPI Feature

## Scope

A skeleton FastAPI application is provided with the following structure already in place:

- `app/main.py` — FastAPI app factory with lifespan and middleware hooks
- `app/config.py` — Settings loaded from environment variables
- `app/auth/api_key.py` — API key authentication dependency
- `app/middleware/logging.py` — Request/response logging middleware
- `app/models/user.py` — SQLAlchemy ORM model + Pydantic schemas
- `app/routes/health.py` — `GET /health` (already working)
- `app/routes/users.py` — `GET /users` and `POST /users` (empty shells)
- `app/services/` — Empty, for candidate use
- `app/utils/database.py` — Async SQLAlchemy engine and session utilities

## Running the App

```bash
# Start PostgreSQL
docker compose up -d

# Install dependencies
uv sync

# Copy and configure environment
cp .env.example .env

# Run the server
uvicorn app.main:app --reload
```

The `/health` endpoint is ready immediately:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```
