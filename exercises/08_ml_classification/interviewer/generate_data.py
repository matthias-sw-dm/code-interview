"""Generates synthetic support tickets (interviewer use only).

Run (from the exercise folder):  uv run python interviewer/generate_data.py
Out:  candidate/tickets.csv             (labelled, 3000 rows)
      candidate/holdout_features.csv    (600 rows, no label)
      interviewer/holdout_labels.csv    (keep private!)

Planted traps (see INTERVIEWER_GUIDE.md):
  - leakage column `resolved_by_team` (only in tickets.csv, equals the label)
  - missing subject / body text
  - ~10% of tickets mention a second topic (ambiguous routing)
  - unseen channel in holdout (`whatsapp`)
  - class imbalance across teams
"""

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
CANDIDATE = HERE.parent / "candidate"
rng = np.random.default_rng(7)

PHRASES = {
    "payments": [
        "my credit card was charged twice",
        "the refund has not arrived yet",
        "paypal payment failed at checkout",
        "the invoice shows the wrong amount",
        "my voucher code is not accepted",
        "direct debit was rejected",
        "I was billed after cancelling my order",
    ],
    "logistics": [
        "my package has not arrived",
        "tracking says delivered but I got nothing",
        "the parcel arrived damaged",
        "I received the wrong item",
        "it was delivered to the wrong address",
        "the pickup point is closed",
        "delivery is already a week late",
    ],
    "account": [
        "I cannot log in anymore",
        "I forgot my password",
        "the password reset email never arrives",
        "please delete my account",
        "I want to change my email address",
        "the two-factor code does not work",
        "my profile shows someone else's data",
    ],
    "app": [
        "the app crashes on startup",
        "the barcode scanner in the app does not work",
        "push notifications are not showing",
        "the app shows a blank screen after the update",
        "I cannot scan my loyalty card in the app",
        "the app is very slow since the last version",
        "the voucher does not show up in the app",
    ],
    "stores": [
        "the store was closed during opening hours",
        "the product was out of stock in the store",
        "the cashier was very rude",
        "the price in the store differs from the shelf label",
        "my click and collect order was not ready",
        "the store was dirty",
        "the queue at the checkout was far too long",
    ],
}
TEAMS = list(PHRASES)
PRIORS = [0.25, 0.30, 0.15, 0.15, 0.15]
OPENERS = ["Hello,", "Hi team,", "Good morning,", "Dear support,", "", ""]
CLOSERS = ["Please help.", "Thanks in advance.", "This is really annoying.", "Can you fix this?", "", ""]
SUBJECTS = {
    "payments": ["Payment problem", "Refund", "Wrong charge", "Voucher", "Invoice"],
    "logistics": ["Order not delivered", "Delivery issue", "Damaged parcel", "Where is my order?"],
    "account": ["Login problem", "Password", "Account", "Cannot sign in"],
    "app": ["App problem", "App bug", "Scanner", "App not working"],
    "stores": ["Store complaint", "Question about my visit", "Click and collect", "Store feedback"],
}


def typo(text):
    words = text.split()
    for i, w in enumerate(words):
        if len(w) > 4 and rng.random() < 0.03:
            j = int(rng.integers(1, len(w) - 1))
            words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2 :]
    return " ".join(words)


def make(n, holdout=False):
    teams = rng.choice(TEAMS, n, p=PRIORS)
    rows = []
    for team in teams:
        parts = [rng.choice(PHRASES[team])]
        if rng.random() < 0.10:  # second, unrelated topic
            other = rng.choice([t for t in TEAMS if t != team])
            parts.append(rng.choice(PHRASES[other]))
        rng.shuffle(parts)
        body = f"{rng.choice(OPENERS)} {' and '.join(parts)}. {rng.choice(CLOSERS)}".strip()
        rows.append((rng.choice(SUBJECTS[team]), typo(body)))
    df = pd.DataFrame(rows, columns=["subject", "body"])
    df.insert(0, "ticket_id", np.arange(n))
    df["channel"] = rng.choice(["email", "chat", "phone", "app"], n, p=[0.45, 0.3, 0.1, 0.15])
    if holdout:
        df["channel"] = np.where(rng.random(n) < 0.03, "whatsapp", df["channel"])
    df["priority"] = rng.choice(["low", "normal", "high"], n, p=[0.3, 0.55, 0.15])
    df["customer_tenure_months"] = rng.integers(0, 120, n)
    # ~3% label noise: tickets that were routed wrongly in the past
    noisy = rng.random(n) < 0.03
    labels = np.where(noisy, rng.choice(TEAMS, n), teams)
    df.loc[rng.random(n) < 0.03, "subject"] = np.nan
    df.loc[rng.random(n) < 0.02, "body"] = np.nan
    return df, labels


if __name__ == "__main__":
    train, y = make(3000)
    train["resolved_by_team"] = y  # leakage
    train["team"] = y
    train.to_csv(CANDIDATE / "tickets.csv", index=False)
    hold, yh = make(600, holdout=True)
    hold["ticket_id"] += 100000
    hold.to_csv(CANDIDATE / "holdout_features.csv", index=False)
    pd.DataFrame({"ticket_id": hold["ticket_id"], "team": yh}).to_csv(HERE / "holdout_labels.csv", index=False)
    print("train class share:\n", pd.Series(y).value_counts(normalize=True).round(3).to_string())
