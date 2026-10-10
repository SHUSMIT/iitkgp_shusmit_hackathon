# RiskPulse: AI/NLP Risk Engine with Strategic Portfolio Stress Testing

**S&P Global & Crisil Campus Hackathon**
**Candidate:** Shusmit Sarkar
**Institute:** IIT Kharagpur
**Selected downstream module:** Module B - Strategic Portfolio Stress Testing

## 1. Problem statement and objective

Financial risk teams receive a continuous stream of unstructured information from news feeds and other public channels. The useful signal is distributed across headlines, summaries, timestamps, publishers, entities, and event descriptions. The objective of RiskPulse is to convert this unstructured stream into structured, machine-readable risk intelligence and connect that intelligence to a practical financial-risk workflow.

The unified engine produces four primary outputs for every article:

- A sentiment score in the range -1 to 1.
- A sentiment label: positive, neutral, or negative.
- An event classification such as Geopolitical, Macroeconomic, Credit Event, Merger/Acquisition, Regulatory/Legal, or Operational/Cyber.
- A 1-10 impact score that identifies events requiring stress analysis.

RiskPulse selects **Module B**, the strategic event-driven portfolio stress-testing application. The module consumes the event classification and impact score, selects the highest-impact event in each detected category, and transmits the corresponding scenario through a synthetic wholesale-banking-style portfolio.

## 2. Solution overview

RiskPulse provides a complete flow from public unstructured data to portfolio-level risk output:

1. Ingest public financial news from Google News RSS and GDELT DOC 2.0. NewsAPI is supported as an optional third source.
2. Normalize article fields and deduplicate records by URL.
3. Apply NLP inference for sentiment, event type, entity references, confidence, and impact.
4. Expose the signals through FastAPI as JSON.
5. Select high-impact events using the score threshold of 7.
6. Apply event-specific market and credit shocks to every portfolio position.
7. Display aggregate before/after portfolio value, loss percentage, scenario assumptions, and asset-level contributions.

The result is a unified risk engine and a working Module B application rather than an isolated classifier.

## 3. Architecture and data flow

### 3.1 System architecture

```text
Google News RSS ─┐
                 ├──> Ingestion and URL deduplication
GDELT DOC 2.0 ───┤
NewsAPI (optional)┘
                         │
                         ▼
                 Unified article records
                         │
                         ▼
              AI/NLP Risk Inference Engine
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   Sentiment       Event class       Impact score
   -1 to 1         + confidence      1 to 10
                         │
                         ▼
                   FastAPI JSON API
                         │
                         ▼
             Module B Stress-Test Engine
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   Market shock      Rate/spread       Credit EL
   beta exposure     duration          PD × LGD
                         │
                         ▼
                 React/Vite dashboard
        portfolio totals, asset losses, related news
```

The architecture diagram is also available in [architecture.png](architecture.png) and [architecture.dot](architecture.dot).

### 3.2 Components

- **Ingestion:** `src/ingestion/sources.py` fetches Google News RSS, GDELT DOC 2.0, and optional NewsAPI records. Each live analysis uses one bounded request per configured source and continues when one source is unavailable.
- **Risk inference:** `src/models/inference.py` combines frozen pretrained sentiment and embedding models, transparent event prototypes, entity matching, and the bundled impact calibration artifact.
- **Workflow/API:** `src/services/workflow.py` coordinates analysis and stress scenarios. `src/api/app.py` exposes `/health`, `/portfolio`, `/analyze`, `/stress-test`, and `/pipeline/run`.
- **Stress engine:** `src/stress/model.py` validates the portfolio, applies event-specific shocks, calculates market and credit effects, and returns position-level results.
- **Dashboard:** `web/src/App.jsx` and `web/src/styles.css` provide source controls, signal inspection, scenario selection, charts, portfolio drill-down, and CSV export.

## 4. Data creation, provenance, and assumptions

The case study refers to sample transaction data, but the organizer does not provide a transaction file in the supplied materials. To make verification possible, this submission includes generated, self-contained data:

- `data/sample_news.csv`: generated financial-news examples covering multiple event types.
- `data/portfolio.csv`: generated 12-position portfolio containing loans, bonds, derivatives, equities, and credit exposures.
- `data/entity_universe.csv`: public entity/ticker lookup used for article-to-position context.
- `data/public_news_snapshot.csv`: public Google News RSS snapshot for reproducible data inspection.

The portfolio includes the sensitivities required by Module B: current value, notional, equity beta, interest-rate duration, spread duration, probability of default, and loss-given-default. Optional sector, counterparty, and ticker columns support related-news matching.

The impact artifact was trained from the public EDT benchmark using the notebook in `notebooks/riskpulse_kaggle_embeddings_xgb.ipynb`. Training provenance and the holdout result are recorded in [KAGGLE_TRAINING.md](KAGGLE_TRAINING.md), [technical_note.md](technical_note.md), and `models/training_report.json`.

The principal scenario assumptions are explicit:

- Impact 7-10 activates stress; impact 1-6 leaves values unchanged.
- Each event class has a defined equity, interest-rate, spread, and PD multiplier shock.
- Severity scales the scenario continuously from the trigger threshold to score 10.
- Credit loss is added for loan, bond, and credit exposures using notional × PD × LGD.
- The displayed loss is a scenario transmission result calculated from the supplied portfolio sensitivities.

## 5. Implementation and requirement coverage

| Case-study requirement | RiskPulse implementation |
|---|---|
| At least two unstructured sources | Google News RSS and GDELT DOC 2.0 are both connected in live mode. |
| Sentiment score | Numeric `sentiment` in [-1, 1] plus `sentiment_label`. |
| Event classification | `event_class` and `event_confidence` for every analyzed record. |
| Impact score | `impact_score` in [1, 10] plus `triggered_stress`. |
| Machine-readable output | FastAPI `/analyze` and `/pipeline/run` return JSON signals and scenarios. |
| Module B | `run_stress` applies event-class-specific shocks to the portfolio. |
| Mixed asset portfolio | 12 generated positions across loans, bonds, derivatives, equities, and credit. |
| High-impact trigger | Impact score >= 7 sets `triggered` to true and applies scaled shocks. |
| Visualization | Dashboard shows portfolio before/after values, losses, scenario shocks, charts, and position details. |
| Verification data | Generated news, portfolio, entity lookup, and public snapshot are included in `data/`. |

## 6. Results and domain impact

The completed workflow provides:

- Structured signals for every source article.
- Event composition and high-impact event counts.
- Source article inspection with publisher, time, summary, and link.
- A selected stress scenario with event class and driver article.
- Portfolio baseline value, stressed value, absolute loss, and loss percentage.
- Scenario shock values for equity, rate, spread, and credit dimensions.
- Position-level market impact, credit-loss increment, stressed value, and loss percentage.
- Position drill-down with beta, duration, spread duration, PD/LGD-driven credit loss, and related analyzed news.
- CSV export of the analyzed signals.

This directly supports the business use case: an analyst can move from an incoming headline to the event classification, understand why it crosses the stress threshold, identify the most affected exposures, and inspect the scenario calculation behind the portfolio result.

## 7. Demonstration and submission plan

The video will demonstrate the complete workflow:

1. Start the API and dashboard using the README commands.
2. Run the bundled generated sample data.
3. Open a signal and show sentiment, event, confidence, impact, and source details.
4. Select a high-impact event and show the Module B stress scenario.
5. Show portfolio before/after values and the asset-level loss chart.
6. Open positions from different asset types and show their sensitivities and credit contribution.
7. Upload a portfolio CSV or news CSV to verify the configurable data path.
8. Run one live-feed analysis to show Google News RSS and GDELT ingestion.
9. Explain the generated verification data and scenario assumptions.

The concise timing script is in [demo_script.md](demo_script.md). The existing six-slide PDF/PPTX can be used as a visual summary, while this report is the detailed written submission.

## 8. Reproducibility and validation

Run the application with the commands in the root [README.md](../README.md). Validation is performed with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Push-Location web
npm run build
Pop-Location
```

The automated suite verifies the health endpoint, sample pipeline, uploaded-news pipeline, stress-trigger behavior, low-impact behavior, and API input bounds.
