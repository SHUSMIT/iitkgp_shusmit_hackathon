# RiskPulse - S&P Global & Crisil Campus Hackathon

## Run it first

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-models.txt
python -m uvicorn src.api.app:app --reload
```

In a second PowerShell terminal:

```powershell
cd web
npm install
npm run dev
```

Open the Vite URL printed in the terminal. The first model-backed run downloads the frozen inference weights and caches them locally. To use the optional conversational analyst or NewsAPI, copy `.env.example` to `.env` and add the relevant local key; never commit `.env`.

## Submission package

This repository contains the complete Module B implementation, source data, architecture diagram, validation tests, and the written submission report in [docs/report.md](docs/report.md). The external guidelines also request a 5–7 slide PDF/PPTX and a 10-minute unlisted walkthrough; the report provides the content and demonstration plan for those submission materials.

Before submission, complete these actions:

1. Verify the public repository and final links.
2. Record the walkthrough using [docs/demo_script.md](docs/demo_script.md).
3. Submit the repository, report/deck, and video links through the official submission form.

## Project overview

RiskPulse is an implemented AI/NLP Risk Engine with a strategic event-driven portfolio stress-testing module. It turns public financial news into structured sentiment, event, and impact signals, then applies those signals to a synthetic wholesale-banking-style portfolio to produce asset-level and portfolio-level stress results.

The platform supports bundled synthetic sample news, a public RSS/GDELT live mode, and uploaded news CSVs. It displays the source article, event type, sentiment, confidence, severity, selected scenario shocks, portfolio before/after value, position-level loss, credit-loss contribution, and related news.

## What is being solved

The system solves event-driven portfolio risk triage. A severity score of 7 or higher activates an event-specific stress scenario; lower scores leave portfolio values unchanged. The result is an explainable scenario calculation with visible shocks, portfolio totals, and asset-level contributions.

## Problem-statement requirement coverage

| Requirement from the case study | Implementation |
|---|---|
| Ingest at least two unstructured-data sources | Live mode makes one bounded request to Google News RSS and one to GDELT DOC 2.0. NewsAPI is an optional third source when a key is configured. |
| Produce a sentiment score from -1 to 1 | Every analyzed article includes numeric `sentiment` and `sentiment_label` fields. |
| Classify the event | Every analyzed article includes `event_class` and `event_confidence`, including categories such as Geopolitical, Macroeconomic, Credit Event, and Merger/Acquisition. |
| Produce an impact score from 1 to 10 | Every analyzed article includes `impact_score`; `triggered_stress` is true at 7 or above. |
| Make signals consumable by downstream applications | FastAPI exposes `/analyze` and `/pipeline/run`; the CLI can write analyzed signals to CSV. |
| Implement at least one downstream module | Module B is implemented as the portfolio stress engine and dashboard. |
| Use a mixed wholesale-banking-style portfolio | The bundled synthetic portfolio contains loans, bonds, derivatives, equities, and credit exposures with beta, duration, spread duration, PD, and LGD. |
| Trigger stress from event class and impact | The workflow selects the highest-impact article in each event class and applies the corresponding scenario when the score is at least 7. |
| Show before/after portfolio impact | The API and dashboard show baseline value, stressed value, total loss, loss percentage, scenario shocks, and asset-level contributions. |

The original prompt refers to “provided sample transaction data,” but no organizer-provided transaction file is present in this repository. The included `data/portfolio.csv` is therefore explicitly synthetic and is used only to demonstrate the required Module B behavior. If an official sample transaction file is supplied later, it can be uploaded through the portfolio CSV control without changing the stress engine.

## Architecture and tech stack

1. The React/Vite dashboard requests the FastAPI workflow.
2. The ingestion layer reads sample/uploaded data or makes one bounded request per available public source.
3. The inference layer produces sentiment, event class, confidence, entity matches, and a 1–10 impact proxy.
4. The stress engine applies transparent event shocks to equity beta, rate duration, spread duration, PD, and LGD.
5. The dashboard renders event signals, scenario results, position details, and optional analyst answers.

Python, FastAPI, pandas, NumPy, XGBoost, scikit-learn, frozen transformer inference, React, Vite, Recharts, and Papa Parse are used. See [docs/architecture.png](docs/architecture.png) and [docs/architecture.dot](docs/architecture.dot).

## Data and assumptions

- `data/sample_news.csv` and `data/portfolio.csv` are synthetic demonstration data.
- `data/public_news_snapshot.csv` is a public RSS snapshot used for reproducibility.
- `data/entity_universe.csv` is a small public company/ticker lookup.
- The impact artifact was trained from the public EDT benchmark; the large raw source is downloaded by the notebook and is not bundled.
- Portfolio shocks are illustrative scenario assumptions. The sample portfolio is not a real person's or institution's portfolio.
- Ticker assignments in the public benchmark and entity matching can be wrong.
- Live sources can be unavailable or rate limited; the app continues with sources that respond and reports an error if all sources fail.
- The impact calibration is trained from a public historical benchmark and recorded in `models/training_report.json`. See [docs/technical_note.md](docs/technical_note.md) for the method.

The portfolio CSV requires `asset_id`, `asset_type`, `current_value`, `notional`, `equity_beta`, `duration`, `spread_duration`, `pd`, and `lgd`. Optional `sector`, `counterparty`, and `ticker` fields improve related-news matching.

## Key results and domain impact

The implemented platform provides an end-to-end path from two public news sources to structured NLP signals and portfolio transmission. It makes event assumptions visible, identifies affected positions, separates current P&L from stressed value, and gives an analyst a repeatable workflow for prioritizing risk review.

## Validation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Push-Location web
npm run build
Pop-Location
```

## Submission metadata

**Candidate Name:** Shusmit Sarkar
**College / Campus:** IIT Kharagpur
**College Email ID:** shusmit.sarkar@gmail.com
**Demo Video Link:** To be added after recording
**Slide Deck:** [docs/presentation.pdf](docs/presentation.pdf)
**Repository:** https://github.com/SHUSMIT/spglobal

## License

MIT. See [LICENSE](LICENSE).
