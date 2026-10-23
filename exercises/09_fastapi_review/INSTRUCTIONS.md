# Exercise 09 - FastAPI Code Review

You have 45 minutes.

## Setup

- This folder contains a small FastAPI service (see `README.md`).
- Requires `python==3.14` and `uv`. No Docker needed.
- You may run the app, call it with curl or the Swagger UI, and use any tooling you normally use.

## Task

Review the code as if it were a merge request a colleague asked you to approve before it goes to production.

1. Read through the code and note every problem you find: bugs, security issues, operational concerns, design smells.
1. For each finding, say **where** it is, **why** it is a problem (what can go wrong, who is affected) and **how** you would fix it.
1. At the end, rank your findings: which ones block the merge, which ones should be follow-ups, which ones are nitpicks?

Think out loud while you review. We will interrupt with questions. You do not have to fix code, but you may sketch a fix if it helps you explain.

## What we look at

- What you find and how deep you go
- How you judge severity and impact
- Whether your fixes are concrete and correct
- How you communicate review feedback
