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

## Submission status and remaining actions

The external guidelines require one public GitHub repository containing working code, dependencies, exact commands, architecture, data, a 5–7 slide PDF/PPTX, and a link to a 10-minute unlisted YouTube walkthrough. They do not require a separate technical report.

Before submission, complete these actions:

1. Confirm the final public repository name follows `<college>-<candidate-name>-hackathon`, and verify it is public in a private browser window.
2. Replace the placeholder candidate, campus, demo-link, and deck-link fields below.
3. Record the walkthrough using the script in [docs/demo_script.md](docs/demo_script.md), show the commands above, and verify the unlisted video in a private browser window.
4. Use the six-slide deck in [docs/presentation.pdf](docs/presentation.pdf) or [docs/presentation.pptx](docs/presentation.pptx); use [docs/presentation_readme.md](docs/presentation_readme.md) as the final content checklist.
5. Submit the repository, video, and deck links through the official submission form before the communicated deadline.

## Project overview

RiskPulse turns public financial news into structured sentiment and event signals, then applies those signals to a portfolio CSV to produce asset-level and portfolio-level stress results. The business problem is to move from a large, noisy headline stream to an explainable view of which positions could be exposed to a market event.

The prototype supports bundled synthetic sample news, a public RSS/GDELT live mode, and uploaded news CSVs. It displays the source article, event type, sentiment, confidence, severity, selected scenario shocks, portfolio before/after value, position-level loss, credit-loss contribution, and related news.

## What is being solved

The system is a decision-support prototype for event-driven portfolio risk triage. It is not a causal news-impact model, a guaranteed price forecast, or a production credit-risk system. A severity score of 7 or higher activates a stress scenario; lower scores leave portfolio values unchanged.

## Architecture and tech stack

1. The React/Vite dashboard requests the FastAPI workflow.
2. The ingestion layer reads sample/uploaded data or makes one bounded request per available public source.
3. The inference layer produces sentiment, event class, confidence, entity matches, and a 1–10 impact proxy.
4. The stress engine applies transparent event shocks to equity beta, rate duration, spread duration, PD, and LGD.
5. The dashboard renders event signals, scenario results, position details, and optional analyst answers.

Python, FastAPI, pandas, NumPy, XGBoost, scikit-learn, frozen transformer inference, React, Vite, Recharts, and Papa Parse are used. See [docs/architecture.png](docs/architecture.png) and [docs/architecture.dot](docs/architecture.dot).

## Data, assumptions, and limitations

- `data/sample_news.csv` and `data/portfolio.csv` are synthetic demonstration data.
- `data/public_news_snapshot.csv` is a public RSS snapshot used for reproducibility.
- `data/entity_universe.csv` is a small public company/ticker lookup.
- The impact artifact was trained from the public EDT benchmark; the large raw source is downloaded by the notebook and is not bundled.
- Portfolio shocks are illustrative scenario assumptions. The sample portfolio is not a real person's or institution's portfolio.
- Ticker assignments in the public benchmark and entity matching can be wrong.
- Live sources can be unavailable or rate limited; the app continues with sources that respond and reports an error if all sources fail.
- The model metric is a small holdout improvement over a median baseline and does not establish reliable predictive value. See [docs/technical_note.md](docs/technical_note.md).

The portfolio CSV requires `asset_id`, `asset_type`, `current_value`, `notional`, `equity_beta`, `duration`, `spread_duration`, `pd`, and `lgd`. Optional `sector`, `counterparty`, and `ticker` fields improve related-news matching.

## Key results and domain impact

The prototype demonstrates an end-to-end path from public news to explainable portfolio transmission. It makes the scenario assumptions visible, shows the affected positions, and separates current portfolio P&L from the illustrative stress result. This helps an analyst prioritize review rather than treating an automated score as a final investment or credit decision.

## Validation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Push-Location web
npm run build
Pop-Location
```

## Submission metadata

**Candidate Name:** SHUSMIT
**College Email ID:** shusmit.sarkar@gmail.com
**College / Campus:** OpenEnv / Copilot
**Demo Video Link:** To be added after recording
**Slide Deck:** [docs/presentation.pdf](docs/presentation.pdf)
**Repository:** https://github.com/SHUSMIT/spglobal

## License

MIT. See [LICENSE](LICENSE).
