# 08 - ML classification: ticket routing

Candidate routes support tickets to the right team: text features, one-hot encoding plus a model of their choice (about 45 min, synthetic data).

- `candidate/` — give to the candidate: `task.py`, `tickets.csv`, `holdout_features.csv`
- `interviewer/` — keep private: `INTERVIEWER_GUIDE.md`, `reference_solution.py`, `generate_data.py`, `holdout_labels.csv`

```bash
uv sync --all-groups --all-packages                   # from the repo root
uv run python candidate/task.py                       # from this directory
uv run python interviewer/reference_solution.py
```
