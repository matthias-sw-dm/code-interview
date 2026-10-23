# 02 - FastAPI refactoring

## Scenario

You have inherited a monolithic FastAPI service called the **Support Portal API**. It manages users and their support requests. The service has JWT authentication and a request-ID middleware — but everything lives in a single `app.py`.

Your task is to read the codebase, describe what you see, plan a refactor, and execute it.

## Running the app

```bash
# from this directory
uv run uvicorn app:app --reload

# API docs available at http://localhost:8000/docs
```

**Test credentials**

| Username | Password | Role |
| -------- | -------- | ----- |
| admin | admin123 | admin |
| analyst | password | user |

## Scope

- ~270-line monolith in `app.py`
- Endpoints: `POST /auth/token`, `GET /users`, `GET /users/me`, `GET /users/{user_id}`, `GET /users/{user_id}/support-requests`, `POST /users/{user_id}/support-requests`
- Business logic (priority detection, categorisation, SLA deadline) embedded directly in route handlers
- Basic JWT authentication
- Request-ID middleware
- Utility helpers with abbreviated names — all in the same file

## Goal

Clean refactored application.

## Process

1. **Describe** the codebase: what does each part do, what are the problems?
1. **Plan** the refactoring: which modules, which responsibilities, what stays in `app.py`?
1. **Execute**: apply the refactor, keep all endpoints working
