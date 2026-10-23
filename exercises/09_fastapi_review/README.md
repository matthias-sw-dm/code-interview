# 09 - FastAPI Code Review

## Scenario

A colleague built the **Voucher API**, a small backend for our customer app. Customers log in, look at their orders and redeem vouchers against their loyalty points. A partner system credits points through a signed webhook. Admins can list and deactivate users.

The colleague says it is *"done, tested manually, ready to merge"* and asks you for a review before it goes to production.

## Running the app

```bash
# from this directory
uv run uvicorn app.main:app --reload

# API docs: http://localhost:8000/docs
```

The app uses a local SQLite file (`vouchers.db`) that is created and seeded on first start. Delete the file to reset the data.

**Seeded accounts**

| Email | Password | Role |
| ------------------- | ---------- | -------- |
| admin@voucher.local | Admin2024! | admin |
| anna@example.com | anna1234 | customer |
| ben@example.com | ben12345 | customer |

## Structure

```
app/
  main.py         # app setup, middleware, error handling, routers
  config.py       # settings (env / .env)
  database.py     # SQLite connection, schema, seed data
  security.py     # password hashing, JWT, auth dependencies
  middleware.py   # request id + request logging
  schemas.py      # pydantic models
  routes/
    auth.py       # POST /auth/login, POST /auth/register
    users.py      # GET/PATCH /users/me, GET /users/search
    orders.py     # GET /orders, GET /orders/{id}, GET /orders/export
    vouchers.py   # POST /vouchers/redeem, POST /webhooks/points
    admin.py      # GET /admin/users, DELETE /admin/users/{id}
```
