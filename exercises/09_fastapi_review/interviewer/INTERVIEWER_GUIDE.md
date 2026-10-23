# Interviewer Guide: FastAPI Code Review (45 min, senior)

**Do not share with the candidate:** the `interviewer/` folder.
**Give the candidate:** everything else (`app/`, `README.md`, `INSTRUCTIONS.md`, `pyproject.toml`).

Setup: `uv run uvicorn app.main:app` from the exercise root. Delete `vouchers.db` between candidates.

15 planted issues, 5 per tier: per tier 3 security issues and 2 conceptual bugs (correctness, data integrity, async/runtime behaviour). The code has no hint comments and passes `ruff`.

Some parts are done right on purpose, and a strong candidate says so: CORS uses an origin allowlist, `require_admin` exists and guards the admin routes, `/users` protects the whole router, SQL is parameterised (the one f-string in `users.py:26` is limited to schema fields, see H1), order lookup checks ownership, pagination is bounded, login returns one generic error, the webhook HMAC uses the raw body and `compare_digest`, and the request id is generated server-side.

## Timeline

| Min | Phase | What you see |
|---|---|---|
| 0–5 | Orient | Reads README, runs the app or at least skims `main.py` → routers → dependencies |
| 5–35 | Review | Goes file by file or follows a request end to end; explains findings as they come |
| 35–45 | Rank and discuss | Blocker vs follow-up vs nit; pick 2–3 discussion questions below |

## Planted issues

### Easy: most candidates should find these

| # | Type | Where | Issue | Expected fix |
|---|---|---|---|---|
| E1 | Security | `config.py:6,11,16,18` | Secrets (JWT secret, admin password, webhook secret) hardcoded as defaults; `debug=True` by default. Anyone with repo access can forge an admin JWT. | No defaults for secrets (fail at startup), secret manager, `debug=False` by default. |
| E2 | Security | `security.py:14` | Unsalted `sha256` for passwords: rainbow tables, fast to brute-force. | argon2id / bcrypt (`pwdlib`), constant-time verify. |
| E3 | Security | `routes/auth.py:17` | `body.model_dump()` logs the **plaintext password** on every login. | Never log credentials; log the user id or a hash of the email only. |
| E4 | Bug | `database.py:29,39`, `schemas.py:37,49` | Money as `REAL` / `float`: rounding errors in totals and voucher values (`0.1 + 0.2`). | Integer cents or `Decimal` / `NUMERIC`; currency field. |
| E5 | Bug | `routes/auth.py:19,30,33` | Email normalisation is inconsistent: `register` stores `email.lower()`, the token carries the raw email and `login` compares case-sensitively. Register as `Max@Example.com` → can never log in with the same input. | Normalise once (in the schema validator), case-insensitive unique index, `EmailStr`. |

### Medium: expected from a senior

| # | Type | Where | Issue | Expected fix |
|---|---|---|---|---|
| M1 | Security | `main.py:43-44` | **Error response leaks internals to the frontend**: `str(exc)` + full traceback (SQL, file paths, library versions). Trigger: register an existing email → 500 with `UNIQUE constraint failed: users.email` + trace. | Generic body (`application/problem+json`) with `request_id` only; details go to logs. Handle `IntegrityError` → 409. |
| M2 | Security | `middleware.py:26-27` | **Request log dumps all headers and the body**: `Authorization` bearer tokens, cookies, passwords from `/auth/login`, PII. Logs end up in Splunk/Datadog with much wider access than the DB. | Allowlist of logged headers, redact `authorization`/`cookie`, never log bodies (or only for specific routes, redacted). |
| M3 | Security | `routes/orders.py:29` | **Auth exists but isn't applied**: `/orders/export` has no `get_current_user` (the router has no router-level dependency, unlike `users.py`). It dumps every customer's email, name and address as CSV without a token. | Router-level `dependencies=[Depends(...)]`; secure by default (global dependency, opt out for `/health`, `/auth/*`); an admin-only export; a test that checks every route needs auth. |
| M4 | Bug | `vouchers.py:72-73`, `schemas.py:56` | **Webhook is not idempotent**: `reference` is accepted and ignored. Partners deliver at-least-once and retry on timeouts → the same points get credited several times. An unknown `user_id` updates 0 rows and still returns 204, so the points are silently lost and the partner never retries. | Unique constraint on `reference` (ledger/inbox table), return 200 on duplicates; check `rowcount` → 404/422. A points **ledger** instead of a mutable counter. |
| M5 | Bug | `routes/orders.py:23` | **Offset pagination over a non-unique, moving sort key**: `ORDER BY created_at DESC` has second resolution (all seed orders share one timestamp → order is undefined) and new orders shift the offset → the client sees duplicates or misses rows between pages. | Tiebreaker (`created_at DESC, id DESC`) and keyset/cursor pagination (`WHERE (created_at, id) < (?, ?)`). |

### Hard: separates strong seniors

| # | Type | Where | Issue | Expected fix |
|---|---|---|---|---|
| H1 | Security | `schemas.py:23` + `users.py:26` | **Mass assignment / privilege escalation**: `UserUpdate.role` is accepted and `PATCH /users/me {"role":"admin"}` writes it. Log in again → admin. The f-string column name looks scary but is limited to schema fields, so the real bug is `role` in the schema. | Separate input schemas per use case; `extra="forbid"`; role changes only via admin endpoint. |
| H2 | Security | `security.py:36,45` | Role trusted from JWT claims, never reloaded: deactivated or demoted users keep access. `verify_exp: False` → tokens **never expire**, so a token leaked through the logs (M2) is valid forever. | Verify `exp`; load the user from DB (or cache) and check `is_active`/role; short-lived access + refresh token; revocation/`token_version`. |
| H3 | Security / Bug | `vouchers.py:34-53` | **Double-spend race (TOCTOU)**: checks `used` and balance, `await`s the fraud check, then writes `points = remaining` (absolute value). Two parallel requests (double-click, mobile retry) both pass and both get the voucher; lost update on points. | Atomic conditional update: `UPDATE vouchers SET used=1 WHERE code=? AND used=0` + check rowcount; `points = points - ? WHERE points >= ?`; one transaction; idempotency key. |
| H4 | Bug | `vouchers.py:19-25` | **Fraud check fails open**: any error (service down, timeout, 500 with HTML body, missing key) → `return True`. The control is silently off exactly when it is under stress, and nobody notices because nothing is logged or measured. Also a new `AsyncClient` (new connection pool) per request. | Decide fail-open vs fail-closed explicitly with the business; log + metric + alert; circuit breaker; shared client created in `lifespan`. |
| H5 | Bug | all routes, e.g. `orders.py:16`, `database.py:45` | **Sync DB calls inside `async def`**: every `sqlite3` call blocks the event loop, so one slow query stalls all concurrent requests (including `/health`). Under load the service looks dead while CPU is idle. | `def` handlers (FastAPI runs them in a threadpool) or an async driver (`aiosqlite`, `asyncpg`, SQLAlchemy async); know the rule "async def only when everything inside awaits". |

### Bonus, not planted on purpose but worth credit

- Business logic and SQL directly in route handlers; no service/repository layer; `dict` instead of a user model.
- `/users/search` lets any customer look up other customers' emails and points.
- No login throttling / brute-force protection.
- Schema created in `lifespan` without migrations; `/health` does not check the DB (liveness vs readiness).
- `/orders/export` builds the whole CSV in memory and wraps a `StringIO` in `StreamingResponse`, which isn't really streaming.
- `BaseHTTPMiddleware` + `await request.body()` buffers every body in memory.
- `settings` is a module-level singleton read at import time, which makes it hard to test.
- JWT secret is shorter than 32 bytes (PyJWT warns at runtime); `HTTP_402` for "not enough points" is unusual.

## Hints (give sparingly, note when used)

- "What does the frontend see when the database throws?" → M1
- "Where does this log line end up, and who can read it?" → E3, M2
- "Which routers protect all their routes, and which protect routes one by one?" → M3
- "The partner's HTTP call times out and they retry. What happens?" → M4
- "A user scrolls through orders while a new order comes in. What does page 2 show?" → M5
- "What happens if the user double-clicks *Redeem*?" → H3
- "The fraud service is down for an hour. What happens?" → H4
- "One query takes 2 seconds. What happens to the other requests?" → H5
- "What can a customer send in this PATCH body?" → H1

## Discussion questions (pick 2–3)

1. **Logging policy:** what may and may not be logged? How do you enforce it (redaction filter, structured logging with allowlisted fields, log access controls, retention)? What if a token already leaked into logs?
1. **Error contract with the frontend:** what goes into a 4xx vs a 5xx body? How does support correlate a user's error with logs (request id)? RFC 9457 problem details.
1. **Secure by default:** how would you make it impossible to forget auth on a new endpoint? (Global dependency + explicit public allowlist, test that enumerates `app.routes`.)
1. **Idempotency and delivery guarantees:** at-least-once webhooks, client retries, idempotency keys, inbox/outbox pattern.
1. **Concurrency:** how do you make redemption correct with 4 uvicorn workers and Postgres? (`SELECT … FOR UPDATE`, conditional update, unique constraints.)
1. **Fail-open vs fail-closed:** who decides, and how do you make the decision visible (metrics, alerts, feature flag)?
1. **Review communication:** how would you phrase the M3 comment to the colleague? Block the MR or approve with follow-ups?

## Scoring (1–4 per row; 4 = strong)

| Dimension | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| Security findings | ≤ 2 of E1–E3 | E1–E3 + 1 of M1–M3 | E1–E3, M1–M3 | Plus H1/H2, connects issues (M2 leaks token + H2 never expires) |
| Bugs / conceptual | None | E4 or E5 | ≥ 1 Medium bug (M4/M5) + Easy bugs | Plus ≥ 1 of H3–H5 with a correct fix |
| Prioritisation | Flat list | Some ordering | Clear blockers vs follow-ups | Ranks by impact × likelihood, knows what to fix first |
| Fix quality | Vague ("make it secure") | Correct direction | Concrete, idiomatic FastAPI fixes | Plus prevention: secure-by-default, tests, constraints in the DB |
| Communication | Silent or harsh | Understandable | Clear, constructive review tone | Explains to the colleague, teaches, acknowledges good parts |

**Rough bar:** mid-level ≥ 11/20. Senior ≥ 15/20 with ≥ 3 in both Security findings and Bugs / conceptual: all 5 Easy, ≥ 4 Medium including **M1, M2, M3**, ≥ 2 Hard, and the blockers ranked correctly.
