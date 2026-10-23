# 06 Java - Backend

You have 60 minutes.

## Setup

- This folder contains an empty Spring Boot project. `./gradlew build` works out of the box.
- Requires JDK 25. Docker is available if you need it.
- Work locally, no need to push anything.
- Use whatever libraries, IDE features and tooling you normally use.

## Task

Build the backend of a multi-user todo application: an HTTP API, a database
behind it, and access control on top.

Talk us through what you are doing while you work. We will interrupt with
questions. If a requirement is ambiguous, ask.

### Domain

- A todo item has a title, an optional description, a due date, a priority and a
  done state.
- Items belong to a list, lists belong to a user.
- Items can be tagged.
- A user can share a list with other users, either read-only or read-write.

### API

- CRUD for lists and items.
- Listing items supports filtering (done state, due date range, tag, text search
  on the title), sorting and pagination.
- Completing or reopening many items in one request.
- Moving an item from one list to another.
- Input validation with a consistent, machine-readable error response.
- Documented endpoints.

### Persistence

- Data lives in a relational database and survives a restart.
- The schema is versioned and applied on startup.
- Indexes fit the queries the API exposes.
- Deleting a list or item is reversible.
- Every row records when and by whom it was created and last changed.
- Two users editing the same item concurrently must not silently overwrite each
  other.

### Security

- No endpoint is reachable without authentication.
- Users can register and log in. Credentials are stored so that a database dump
  does not reveal them.
- A user only sees and modifies their own lists and the lists shared with them,
  regardless of which IDs they pass.
- There is an admin role that can list all users and all lists.
- Sessions or tokens expire.
- Repeated failed logins are throttled.

### Quality

- Business logic is unit tested; the API is covered by integration tests,
  including the access control rules. Not every class needs a real test here —
  but make it clear what you would test and how, even if that is an empty test
  class with a few comments in it.
- Clear separation between transport, business logic and persistence, and
  between the API contract and the persistence model.
- Logs are structured and contain no credentials or tokens.
- The service exposes health and metrics endpoints.

### Delivery

- Configuration differs per environment; no secrets in the repository.
- The service can be built and run as a container.
- A short README explains how to run it and how to call the API.

## What we look at

- How you structure the code and where you draw boundaries.
- Your data model.
- Whether the access control actually holds.
- What you test and why.
- How you decide, and how you explain those decisions to us.
