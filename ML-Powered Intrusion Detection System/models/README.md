# Models

Place your trained artifacts here (they are git-ignored):

- `binary_model.joblib` – benign vs malicious classifier
- `attack_model.joblib` – attack-type classifier
- `label_encoder.joblib` – converts attack-type integers to names
- `feature_columns.json` – (recommended) ordered list of training feature columns

Export them from your Phase 1/2 notebooks with `joblib.dump(model, "binary_model.joblib")`.
