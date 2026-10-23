# Interviewer guide: ticket routing with text features and one-hot encoding

Give the candidate everything in `candidate/`. Keep `interviewer/` private.
Teams: payments, logistics, account, app, stores. Run `interviewer/reference_solution.py` for the reference result.

## What to look for

| Topic | Good behaviour |
|---|---|
| Leakage | `resolved_by_team` equals the label and is missing in the holdout. Candidate drops it. |
| IDs | Drops `ticket_id`. |
| Text | Combines subject and body, uses a vectorizer (TF-IDF or bag of words). Handles missing text. |
| One-hot encoding | `handle_unknown="ignore"`. Holdout contains the unseen channel `whatsapp`, the default encoder crashes. |
| Imbalance | Stratified split, macro-F1 / per-class report instead of accuracy only. |
| Ambiguity | ~10% of tickets mention two topics, ~3% of labels are wrong. Candidate does not expect 100%. |
| Fitting | Vectorizer and encoder fitted on training data only. |

## Discussion (pick 2-3)

1. Bag of words / TF-IDF vs embeddings vs an LLM for this task. When is the extra effort worth it?
1. What should happen with low-confidence predictions? (Fallback queue, human triage.)
1. What does a misrouted ticket cost? Per-team precision vs recall.
1. How would you notice that new topics appear over time? (Drift, retraining.)
1. How do you keep training and serving preprocessing identical?

## Hints

- Stuck: "What happens at predict time if a channel never occurred in training?"
- No leakage found: "Which columns would exist when a new ticket arrives?"
- Accuracy only: "How does a model that always predicts the biggest team score?"

## Holdout check

Compare `predictions.csv` with `interviewer/holdout_labels.csv`. The reference reaches macro-F1 ≈ 0.96. Below ≈ 0.85 suggests a bug or missing text features.
