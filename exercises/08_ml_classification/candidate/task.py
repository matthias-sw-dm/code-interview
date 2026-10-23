"""
Task: route support tickets to the right team
=============================================

`tickets.csv` contains past tickets with the team that handled them (`team`).
`holdout_features.csv` has no label.

1. Take a quick look at the data.
2. Turn the ticket text into features and one-hot encode the categorical columns.
   Train a model of your choice.
3. Evaluate it and explain which metric you picked.
4. Predict the holdout file and write `predictions.csv` (ticket_id, team).

Docs / Google allowed, no AI assistants. Please think aloud.

Feel free to ask questions about the use case (e.g. what a wrong prediction
costs, how the model will be used or whatever). Your answers should guide your decisions.
"""

from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent

df = pd.read_csv(HERE / "tickets.csv")
holdout = pd.read_csv(HERE / "holdout_features.csv")

# TODO
