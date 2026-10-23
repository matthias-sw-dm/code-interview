"""Reference solution (interviewer use only): TF-IDF on the text + one-hot encoding + logistic regression."""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HERE = Path(__file__).parent
CANDIDATE = HERE.parent / "candidate"

# Columns the candidate should use:
TEXT = ["subject", "body"]  # TF-IDF (joined into one string)
CATEGORICAL = ["channel", "priority"]  # one-hot encoding
NUMERIC = ["customer_tenure_months"]  # standardised
# Columns the candidate should NOT use:
#   ticket_id         identifier
#   resolved_by_team  leakage: equals the label and is missing in the holdout
#   team              the target

# --- Load and clean ---------------------------------------------------------
df = pd.read_csv(CANDIDATE / "tickets.csv")
holdout = pd.read_csv(CANDIDATE / "holdout_features.csv")

y = df["team"]
X = df[TEXT + CATEGORICAL + NUMERIC]


def text_of(X_new):
    """Subject and body as one string, missing text becomes empty."""
    return X_new[TEXT].fillna("").agg(" ".join, axis=1)


def fit(X_train, y_train):
    """Learn the features + model on the training data only, return a function that predicts teams."""
    # TF-IDF on the ticket text: unigrams + bigrams, words in fewer than 2 tickets are ignored.
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    vectorizer.fit(text_of(X_train))

    # Unseen channel (e.g. "whatsapp") becomes all zeros instead of crashing.
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    encoder.fit(X_train[CATEGORICAL])

    scaler = StandardScaler()
    scaler.fit(X_train[NUMERIC])

    def to_features(X_new):
        text = vectorizer.transform(text_of(X_new))
        categorical = encoder.transform(X_new[CATEGORICAL])
        numeric = scaler.transform(X_new[NUMERIC])
        return hstack([text, np.hstack([categorical, numeric])]).tocsr()

    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(to_features(X_train), y_train)

    return lambda X_new: model.predict(to_features(X_new))


# --- Evaluate on a validation split ----------------------------------------
# Stratified, classes are imbalanced. Macro-F1 treats every team equally, accuracy would favour big teams.
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=0)
predict = fit(X_train, y_train)
p_val = predict(X_val)
print(f"val macro-F1={f1_score(y_val, p_val, average='macro'):.3f}  accuracy={(p_val == y_val).mean():.3f}")
print(classification_report(y_val, p_val))

# --- Retrain on all labelled data and predict the holdout ------------------
predict = fit(X, y)
predictions = pd.DataFrame({"ticket_id": holdout["ticket_id"], "team": predict(holdout[X.columns])})
predictions.to_csv(HERE / "predictions.csv", index=False)

# --- Score against the private holdout labels ------------------------------
labels = pd.read_csv(HERE / "holdout_labels.csv")
scored = predictions.merge(labels, on="ticket_id", suffixes=("_pred", "_true"))
print(
    f"holdout macro-F1={f1_score(scored['team_true'], scored['team_pred'], average='macro'):.3f}  "
    f"accuracy={(scored['team_true'] == scored['team_pred']).mean():.3f}"
)
