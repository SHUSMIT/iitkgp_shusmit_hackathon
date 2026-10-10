# Presentation and pitch checklist

The submission guidelines require **5–7 slides** in PDF or PPTX. This repository contains a six-slide deck in `presentation.pdf` and `presentation.pptx`. There is no separate report deliverable in the guidelines.

## Slide content

1. **Title:** RiskPulse, candidate name, college/campus, and the one-line use case.
2. **Problem and approach:** Explain the headline-to-portfolio triage problem, the input sources, and the output.
3. **System design:** Show the architecture diagram and the flow from ingestion to inference to stress transmission.
4. **Implementation:** Explain the API/dashboard split, public/synthetic data, transparent event shocks, and why the pipeline is explainable.
5. **Results:** Show the dashboard, a high-impact event, the 7+ trigger, before/after portfolio values, and position-level loss. State the holdout MAE and median baseline honestly.
6. **Domain impact and limitations:** Explain analyst prioritization, then state synthetic portfolio data, illustrative shocks, imperfect ticker assignments, partial live feeds, and that the score is not a causal forecast.

## What to say in the live pitch

- “We are solving event-driven risk triage: converting noisy public headlines into an explainable list of portfolio exposures for analyst review.”
- “The engine consumes two live public sources in one run: Google News RSS and GDELT DOC 2.0. NewsAPI is an optional third source when a key is available.”
- “Each article becomes a machine-readable sentiment score, event classification, confidence, and 1–10 impact score through the API.”
- “We selected Module B, the strategic event-driven portfolio stress tester, rather than Module A.”
- “The stress result is scenario analysis. It is not a claim that the headline caused the exact loss shown.”
- “A score of 7 or above is the explicit trigger. Beta, duration, spread duration, PD, and LGD determine each position’s transmission.”
- “The sample portfolio and sample news are synthetic because no organizer-provided transaction CSV is included in this repository; the dashboard accepts a replacement portfolio CSV.”
- “The live feeds are public and can be incomplete or rate limited.”
- “The next production step is calibration against validated issuer mappings, historical portfolios, and later time periods.”

## 10-minute demonstration sequence

1. **0:00–0:30:** State the problem and what the dashboard produces.
2. **0:30–1:00:** Start the API and web app using the README commands.
3. **1:00–3:30:** Run the included sample, open a headline, and explain event, sentiment, confidence, severity, and source link.
4. **3:30–6:00:** Select the triggered scenario, show portfolio before/after values, shocks, and the asset-loss chart.
5. **6:00–7:30:** Open a position and show beta, duration, spread duration, credit loss, P&L, and related news.
6. **7:30–8:15:** Upload a portfolio CSV or news CSV to prove the input path is not hard-coded.
7. **8:15–9:00:** Fetch live public feeds once, show that Google News and GDELT are the two configured sources, and explain that partial-source failures are surfaced.
8. **9:00–10:00:** State the requirement coverage, limitations, holdout result, and next validation steps.

Do not claim that the prototype predicts guaranteed returns, uses confidential data, or represents a real client or person's portfolio.
