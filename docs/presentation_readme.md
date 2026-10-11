# Recorded presentation script: what to show and what to say

This is the exact script for the 10-minute recorded walkthrough. Follow the screen actions and use the narration below. The recording should show the running application, not a slide presentation.

## Before recording

1. Start the FastAPI server and React/Vite dashboard using the commands in the root [README.md](../README.md).
2. Open the dashboard in the browser.
3. Keep the terminal visible briefly at the beginning so the evaluator can see that the application is running.
4. Use the bundled sample data first. Fetch live feeds only once near the end.

## 0:00-0:45 — Introduction and objective

### Show

- The running RiskPulse dashboard.
- The title, “Portfolio analysis,” and the analysis controls.

### Say

“Hello, I am Shusmit Sarkar from IIT Kharagpur. This is RiskPulse, my unified AI/NLP Risk Engine for the S&P Global and Crisil case study. I selected Module B, Strategic Portfolio Stress Testing.”

“The problem is to convert unstructured financial news into structured risk signals and then show how a high-impact event can affect a portfolio of wholesale-banking-style assets. The system produces sentiment, event classification, confidence, and an impact score for each article. Module B consumes those signals and calculates portfolio stress.”

## 0:45-1:30 — Running application and data choices

### Show

- The FastAPI terminal with the server running.
- The browser dashboard.
- The source selector set to **Sample portfolio news**.
- The portfolio CSV control and the Run analysis button.

### Say

“The application has a FastAPI backend and a React dashboard. The bundled data is included so the evaluator can run the complete workflow immediately and reproduce the results.”

“The sample news and the 12-position portfolio are generated verification data. The portfolio contains loans, bonds, derivatives, equities, and credit exposures with current value, notional, equity beta, duration, spread duration, probability of default, and loss-given-default.”

“The case study refers to provided transaction data, but no transaction file was supplied with the case materials. Therefore, I created and included this representative portfolio dataset for verification. The application also accepts a replacement portfolio CSV.”

## 1:30-2:30 — Run the unified risk engine

### Show

- Click **Run analysis**.
- Wait for the results.
- Show the article count and portfolio position count.
- Keep the signal table visible.

### Say

“I am now running the complete pipeline. The engine reads the article records, normalizes the fields, removes duplicate URLs, and generates a structured signal for every article.”

“The result contains a sentiment score between minus one and one, an event class, event confidence, and a one-to-ten impact score. These structured records are also available through the FastAPI endpoints `/analyze` and `/pipeline/run` for downstream use.”

## 2:30-3:45 — Explain one signal in the dashboard

### Show

- Sort or scan the signal table by severity.
- Click a high-impact news row.
- Show the article title, publisher, timestamp, summary, event, sentiment, impact, confidence, and source link.

### Say

“Each row is one analyzed news event. I will open this row to show the complete signal. The source headline and metadata are retained, while the engine adds the event class, sentiment, confidence, and impact.”

“The event class is the bridge into Module B. The impact score determines whether the event should trigger stress. In this implementation, an impact score of seven or above activates the corresponding stress scenario.”

“This makes the result traceable: the reviewer can move from the portfolio loss back to the source article and the structured event signal that caused the scenario selection.”

## 3:45-5:30 — Demonstrate Module B stress testing

### Show

- Close the article detail.
- Scroll to **Portfolio analysis**.
- Open the stress scenario selector.
- Select a scenario marked as triggered.
- Show stressed portfolio value, baseline value, net loss, loss percentage, scenario driver, and shock tags.

### Say

“This is the selected downstream application, Module B: Strategic Portfolio Stress Testing. The workflow groups analyzed events by event class and chooses the highest-impact event in each class for scenario evaluation.”

“For a triggered event, the stress engine applies the event-specific equity shock, rate shock, spread shock, and probability-of-default multiplier. The severity score scales the shock continuously. The dashboard shows the baseline portfolio value, the stressed value, the absolute loss, the loss percentage, and the exact scenario driver.”

“This is the required before-and-after portfolio visualization from the case study.”

## 5:30-6:45 — Demonstrate asset-level transmission

### Show

- Show the net impact by position chart.
- Click one loan or bond.
- Show opening value, closing value, current P&L, scenario loss, beta, duration, spread duration, and credit loss.
- If possible, click an equity or derivative position afterward.

### Say

“The result is not only a portfolio total. The engine preserves the contribution of every position.”

“For market-sensitive positions, equity beta, interest-rate duration, and spread duration transmit the scenario shock into the asset value. For loans, bonds, and credit exposures, the engine also calculates an incremental expected credit loss using notional, probability of default, and loss-given-default.”

“This position-level view explains which exposures drive the portfolio result and why different asset types respond differently to the same event.”

## 6:45-7:30 — Demonstrate configurable input data

### Show

- Close the position detail.
- Show the Portfolio CSV upload control.
- Optionally show the News CSV upload control.
- Do not spend time changing the file if the sample run is already complete.

### Say

“The workflow is data-configurable rather than hard-coded to one screen. A reviewer can upload a portfolio CSV using the documented schema, or upload a news CSV with article fields. The same analysis and stress engine then processes the supplied records.”

## 7:30-8:45 — Demonstrate two-source live ingestion

### Show

- Change the source selector to **Google News + GDELT feeds**.
- Keep the default lookback and article limit.
- Click **Run analysis once**.
- Show the resulting article count and source labels.

### Say

“The core engine requirement asks for at least two unstructured-data sources. Live mode connects Google News RSS and GDELT DOC 2.0 in the same workflow. NewsAPI is also supported when an API key is configured.”

“I am making one live request now. The application deduplicates the returned articles and continues with whichever public sources respond. The source metadata remains visible in the signal details.”

## 8:45-9:30 — Explain the architecture

### Show

- Open [docs/architecture.png](architecture.png) or show the architecture diagram in the repository.
- If staying in the dashboard, point to the flow already demonstrated.

### Say

“The architecture has five stages. First, public news sources provide unstructured articles. Second, the ingestion layer normalizes and deduplicates them. Third, the AI/NLP risk engine adds sentiment, event classification, confidence, entity references, and impact. Fourth, FastAPI exposes the structured output and connects it to the stress engine. Fifth, the React dashboard visualizes the signals, scenarios, and position-level results.”

“This separation allows the risk engine output to be consumed by Module B through the API and also makes each stage independently testable.”

## 9:30-10:00 — Close with completed outcome

### Show

- Return to the portfolio result or the dashboard summary.
- Leave the triggered scenario and asset-level results visible.

### Say

“To conclude, RiskPulse implements the unified AI/NLP Risk Engine and Module B, Strategic Portfolio Stress Testing. It ingests two public news sources, produces machine-readable sentiment, event, and impact signals, triggers event-specific stress scenarios, and shows portfolio and position-level effects using generated verification data.”

“The repository contains the source code, data, architecture, tests, setup commands, and detailed report needed to reproduce this workflow.”

## Recording checklist

The final video must visibly include:

- The running API and dashboard.
- The sample analysis.
- A structured signal with sentiment, event class, confidence, and impact.
- A source article detail.
- A triggered Module B scenario.
- Portfolio before and after values.
- Event shock values.
- Asset-level loss visualization.
- A position detail with beta, duration, spread duration, and credit loss.
- The generated portfolio data explanation.
- One live run using Google News RSS and GDELT.
- The architecture and API-to-dashboard flow.
