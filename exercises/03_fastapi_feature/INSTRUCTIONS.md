# Exercise 03 - FastAPI Feature

You have 60 to 90 minutes.

## Setup

- This folder contains a skeleton of a FastAPI application.
- Requires `python==3.14`, `uv` and `docker-compose` installed
- Works locally
- You can use any libraries you want and any tooling you normally use

## Task

Build the backend of a multi-user todos application, an HTTP API, a postgres database and access control on top.

We expect you to walk us through what you are doing while you work. We will interrupt if we have questions. If something is unclear ask.

## Domain

- A `User` has id (uuid), email and first/last name
- A `Todo` has title, description, due date, priority and done state
- `Todo` belong to a `List` and a `List` belongs to a `User`

## API

- CRUD for lists, todos and users
- Listing todos support filtering (done state, due date range, tax, text search on title), sorting and pagination
- Input validation with machine-readable error responses
- Documented endpoints

## Persistence

- Data lives in `postgres` and survives restart
- Schema is versioned and applied on startup
- Indexes fit the queries the API exposes
- Deleting a list or item is reversible
- Every row record when and by whom it was created and last changed
- Two users editing the same item concurrently must not silently overwrite each other

## Security

- No endpoint is reachable without authentication
- Users can register and log in. Credentials are stored, so that in a leak they are not revealed
- User only sees and modifies their own lists
- Repeated failed requests are throttled

## Quality

- Business logic is unit tested
- API is covered by integration tests, including access control rules
- Clear separation between transport, business logic and persistence
- Logs are structured
- Service expose health and metric endpoints

## CI/CD

- Configuration differs per environment
- The service can be built
- Short README explains how to run it and how to call the API

## What we look at

- How you structure the code and where you set boundaries
- Data model
- Access control and testing
- Testing methodology
- How you decide and how you explain those decisions
