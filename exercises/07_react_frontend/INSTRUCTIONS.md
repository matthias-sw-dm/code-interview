# 07 React - Frontend

You have 60 minutes.

## Setup

- This folder contains an empty Vite + React + TypeScript project. `pnpm install`,
  then `pnpm dev`, works out of the box.
- `pnpm mock` starts the mock backend on port 4000, `pnpm dev` proxies `/api` to
  it. You need both running.
- Requires Node 24 and pnpm. Work locally, no need to push anything.
- Use whatever libraries, IDE features and tooling you normally use.
- Log in as `ada@example.com` or `grace@example.com`, password `demo`.
- The mock adds 150-500ms of latency and drops roughly 15% of all writes with a
  500\. `LATENCY=0 FAIL_RATE=0 pnpm mock` turns both off while you debug.
- Data lives in memory and resets whenever the mock restarts.

## Task

Build the frontend of a multi-user todo application against the mock API
documented below.

Talk us through what you are doing while you work. We will interrupt with
questions. If a requirement is ambiguous, ask.

### UI drafts

`docs/` holds three sketches: `01-desktop-list.png`, `02-item-detail.png` and
`03-mobile-list.png`. They are hints about structure, not a design spec -
deviate where you have a reason and tell us the reason. There is no draft for
the login screen, that one is yours.

### Screens

- Log in, log out, and stay logged in across a reload.
- A list overview next to the items of the selected list.
- An item detail view for editing, as a drawer or a dialog.
- The URL carries the state: selected list, filters, sort, page, open item.
  Reload, back and forward keep working, and a shared URL opens the same view.

### Lists and items

- Create, rename and delete lists.
- Create, edit and delete items: title, description, due date, priority, tags.
- Toggle done straight from the row, without opening the detail view.
- Select several rows and complete or reopen them in one request.
- Move an item to another list.
- Editing tags suggests the tags that already exist.
- Deleting offers an undo; the API can restore an item.

### Filtering, sorting, paging

- Filter by done state, due date range, tag and text search on the title.
- Search is debounced and typing stays responsive.
- Sort by due date, priority, title and creation date, ascending and descending.
- Paging including page size. `Backlog` has 500 items - make that list usable.

### Data and state

- Writes feel instant and roll back when the request fails.
- A read-only list offers no edit affordances, and a 403 is still handled.

### Failure and feedback

- Loading, empty and error states per view, not one spinner over everything.
- A failed write keeps the user's input, says what happened and offers a retry.
- A 409 on save shows what changed and lets the user decide.
- A 401 goes back to login without losing where the user was.
- A throttled login (429) tells the user how long to wait.

### Quality

- The API layer is typed and nothing crosses that boundary as `any`.
- Components are small enough to test. Test the parts that carry logic - filter
  state, optimistic updates, conflict handling. Not every component needs a real
  test here, but make it clear what you would test and how, even if that is a
  test file with a few comments in it.
- Keyboard reachable, labelled controls, focus handled in the dialog, async
  updates announced to screen readers.
- Responsive down to the mobile draft, light and dark mode.
- German and English, dates and numbers formatted per locale.

### Delivery

- `pnpm build` and `pnpm lint` pass.
- A short README explaining how to run it, what you built, and what you left out.

## The mock API

Everything except the login needs an `Authorization: Bearer <token>` header.

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/auth/login` | `{email, password}` -> `{token, user}`. 401 on wrong credentials, 429 after five failures |
| GET | `/api/auth/me` | the current user |
| GET | `/api/lists` | `[{id, name, role, owner, itemCount, openCount}]`, role is `owner`, `write` or `read` |
| POST | `/api/lists` | `{name}` |
| PATCH | `/api/lists/:id` | `{name}`, owner only |
| DELETE | `/api/lists/:id` | owner only |
| GET | `/api/lists/:id/items` | `?done=&q=&tag=&dueFrom=&dueTo=&sort=&page=&pageSize=` -> `{items, page, pageSize, total}` |
| POST | `/api/lists/:id/items` | `{title, description?, dueDate?, priority?, tags?}` |
| GET | `/api/items/:id` | |
| PATCH | `/api/items/:id` | partial update, must include the `version` you loaded |
| DELETE | `/api/items/:id` | soft delete |
| POST | `/api/items/:id/restore` | undoes a delete |
| POST | `/api/items/:id/move` | `{listId}` |
| POST | `/api/items/bulk` | `{ids, done}` -> `{updated, failed}`, partial success is possible |
| GET | `/api/tags` | `[{name, count}]` across all lists you can see |

- `tag` can be repeated and then means "has all of these tags". `sort` is one of
  `due`, `priority`, `title`, `created`, prefixed with `-` for descending.
  `pageSize` defaults to 25 and caps at 100.
- Errors look like `{"error": {"code": "...", "message": "...", "fields": {...}}}`.
  You will see 401, 403, 404, 409, 422, 429 and 500.
- A `PATCH` with a stale `version` returns 409 and the current item under
  `error.current`.
- `Household` is shared with Ada read-only, `Team Retro` read-write. Log in as
  Grace in a second browser profile if you want to provoke conflicts.
- `mock-api/server.mjs` is a single dependency-free file. Read it if something
  surprises you, but you should not have to change it.

## What we look at

- How you split components and where you keep state.
- How you talk to the API and what happens when it misbehaves.
- What you test and why.
- How you prioritise, and how you explain those decisions to us.
