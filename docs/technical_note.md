# Technical note

## Inference and event severity

FinBERT sentiment and MiniLM sentence embeddings are optional, frozen pretrained models. MiniLM compares article text with a small set of transparent event prototypes. When the Kaggle artifacts are installed, XGBoost predicts the absolute next-day single-stock price move from the same frozen MiniLM vector. Without those artifacts, exact risk terms drive event classification and a documented rule provides fallback severity.

The trained target is the log absolute next-day price move from the EDT news/market benchmark. The output is scaled to 1–10 using training-set movement quantiles. This is a market-movement proxy, not a causal event impact or portfolio-loss forecast. A time-ordered holdout is compared against a median baseline before retaining the model.

The current prototype used 50,000 rows from the 75,395 records remaining after date, price, and ticker-text checks. On the latest 10,000 rows, MAE was 1.699 percentage points versus 1.731 for a train-median baseline (about 1.8% lower). This is a small improvement and does not establish reliable predictive value. See `models/training_report.json`; retrain and evaluate across later periods and ticker groups before relying on the learned score.

## Stress calculation

For each portfolio asset, the engine applies equity beta, rate duration, and spread duration to event-specific scenario shocks. It separately adds incremental expected credit loss for loans, bonds, and credit exposures. Scores below 7 leave portfolio values unchanged. Higher scores scale the scenario continuously, and the output retains per-asset contributions.

## Scope and next data requirement

The sample portfolio is synthetic and event shocks are illustrative assumptions. The EDT source notes that ticker assignments can be wrong. Validate by date and ticker, calibrate scenario sizes separately, and track data and model drift. The current MVP does not link named issuers to portfolio counterparties or aggregate correlated events.
