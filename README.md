# RiskPulse - S&P Global & Crisil Campus Hackathon

**Candidate Name:** SHUSMIT  
**College Email ID:** shusmit.sarkar@gmail.com  
**College / Campus:** OpenEnv / Copilot  
**Demo Video Link:** To be added after recording  
**Slide Deck:** [docs/presentation.pdf](docs/presentation.pdf)  
**Repository:** https://github.com/SHUSMIT/spglobal

## 1. Project overview / problem statement and approach

RiskPulse turns public financial news into AI-generated sentiment and event signals, then applies those signals to a portfolio CSV to produce asset-level and portfolio-level stress results.

## Project overview

The system ingests Google News RSS, GDELT DOC 2.0, NewsAPI (when a key is configured), or an uploaded news CSV. FinBERT produces sentiment, MiniLM produces frozen text embeddings, and a bundled XGBoost model estimates a 1-10 market-impact proxy. The output is passed to a transparent portfolio stress engine using equity beta, rate duration, spread duration, probability of default, and loss-given-default.

The portfolio is supplied as CSV. Every position can be opened in the dashboard to inspect its sensitivities, scenario loss, credit-loss contribution, and related analyzed news. Clicking a news row opens the source link together with the AI event, sentiment, confidence, and impact analysis.

## 2. Architecture and tech stack

See [docs/architecture.png](docs/architecture.png) and [docs/architecture.dot](docs/architecture.dot).

- Python, FastAPI, pandas, NumPy, XGBoost, scikit-learn
- FinBERT and sentence-transformers/all-MiniLM-L6-v2
- React, Vite, Recharts, Papa Parse
- Google News RSS, GDELT DOC 2.0, optional NewsAPI
- CSV portfolio and news inputs

## 3. Dataset used

- `data/sample_news.csv`: synthetic demonstration news.
- `data/portfolio.csv`: synthetic portfolio positions and sensitivities.
- `data/entity_universe.csv`: public company/entity lookup used for ticker mentions.
- `data/public_news_snapshot.csv`: public Google News RSS snapshot.
- The XGBoost artifact was trained from the public EDT benchmark described in [docs/KAGGLE_TRAINING.md](docs/KAGGLE_TRAINING.md). The large raw benchmark is downloaded on demand and is not copied into this repository.

The trained target is a next-day single-stock movement proxy, not a causal event impact or a guaranteed portfolio-loss forecast. Portfolio shocks are explicit scenario assumptions and are shown per position.

### Portfolio CSV schema

Required columns are `asset_id`, `asset_type`, `current_value`, `notional`, `equity_beta`, `duration`, `spread_duration`, `pd`, and `lgd`. Optional `sector` and `counterparty` columns improve news matching. An optional `ticker` column (for example `AAPL`) can be added when a position should be associated with a listed issuer; related analyzed headlines are then matched against the ticker, issuer, counterparty, and sector.

## 4. Quickstart and installation

Runtime tested: Python 3.13, Node.js 20+, Windows.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-models.txt
```

The first model-backed run downloads FinBERT and MiniLM weights from Hugging Face and caches them locally. Pretrained inference is always used by the dashboard and API; there is no model-selection toggle in the UI.

Optional NewsAPI configuration is local-only:

```powershell
Copy-Item .env.example .env
# edit .env and set NEWSAPI_KEY
```

Never commit `.env` or publish the key.

For the conversational analyst, add `GROQ_API_KEY` to the same local `.env`. The dashboard sends the complete analyzed-news set, plus the selected position when one is open, to the configured Groq model. If the key is absent, the UI reports that configuration error explicitly.

Start the backend:

```powershell
.venv\Scripts\python.exe -m uvicorn src.api.app:app --reload
```

In a second terminal, start the dashboard:

```powershell
cd web
npm install
npm run dev
```

Open the Vite URL shown in the terminal. Choose sample news, live public feeds, or a news CSV. A portfolio CSV can be uploaded; otherwise `data/portfolio.csv` is loaded through the API.

## News source queries

- Google News RSS uses the `q` parameter, for example `banking OR inflation OR recession when:1d`.
- GDELT DOC 2.0 uses `query`, `mode=ArtList`, `format=json`, `maxrecords`, `timespan`, and `sort=datedesc`. The application sends a boolean query such as `(bank OR markets OR inflation OR rates OR recession OR sanctions OR merger OR default OR liquidity)`.
- NewsAPI uses `/v2/everything` with `q`, `language`, `pageSize`, `sortBy`, and `apiKey`.

GDELT and NewsAPI are external services. GDELT can return HTTP 429 during rate limiting; the application retries briefly and continues with sources that are available. NewsAPI requires a valid key and plan quota.

## 5. Key results and domain impact

The prototype demonstrates an end-to-end flow from news ingestion through pretrained NLP inference, impact scoring, portfolio transmission, asset-level P&L, and conversational risk reasoning. It is designed for a transparent hackathon demonstration: scenario shocks are explicit assumptions, while the AI output is an analytical aid rather than a guaranteed forecast.

## Tests and build

```powershell
.venv\Scripts\python.exe -m pytest -q
cd web
npm run build
```

## Key outputs

The dashboard presents:

- AI sentiment, event class, confidence, and impact per article.
- Source metadata and a link to the full article.
- Scenario-level portfolio before/after values and losses.
- Asset-level beta, duration, spread, credit-loss, and scenario-loss details.
- Position opening value, closing value, and P&L.
- Related analyzed news for the selected portfolio position.
- Conversational reasoning over all analyzed news or a selected position when Groq is configured.

## License

MIT. See [LICENSE](LICENSE).
