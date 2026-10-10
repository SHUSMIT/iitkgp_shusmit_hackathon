# Technical note: RiskPulse Module B

## Inference and event severity

FinBERT sentiment and MiniLM sentence embeddings are optional, frozen pretrained models. MiniLM compares article text with a short reference description of each event class. When the Kaggle artifacts are installed, XGBoost predicts the absolute next-day single-stock price move from the same frozen MiniLM vector. Without those artifacts, exact risk terms drive event classification and a documented rule-based score provides severity.

The trained target is the log absolute next-day price move from the EDT news/market benchmark. The output is scaled to 1–10 using training-set movement quantiles. This is a market-movement proxy, not a causal event impact or portfolio-loss forecast. A time-ordered holdout is compared against a median baseline before retaining the model.

The implementation used 50,000 rows from the 75,395 records remaining after date, price, and ticker-text checks. On the latest 10,000 rows, MAE was 1.699 percentage points versus 1.731 for a train-median baseline. The result is recorded in `models/training_report.json` and establishes the impact calibration used by the engine.

## Stress calculation

For each portfolio asset, the engine applies equity beta, rate duration, and spread duration to event-specific scenario shocks. It separately adds incremental expected credit loss for loans, bonds, and credit exposures. Scores below 7 leave portfolio values unchanged. Higher scores scale the scenario continuously, and the output retains per-asset contributions.

## Data and operating assumptions

The project supplies generated sample news and a generated 12-position portfolio because no organizer transaction data was provided. The dashboard accepts replacement CSV data. The engine uses explicit event shocks and preserves every position-level contribution so the result can be verified.

## Architecture

Ingestion produces normalized article records, the inference layer adds structured NLP fields, the FastAPI workflow selects high-impact events, and the stress engine applies market and credit transmission to the portfolio. The React dashboard consumes the workflow JSON and renders the complete Module B result. The architecture diagram is in `docs/architecture.png`.
