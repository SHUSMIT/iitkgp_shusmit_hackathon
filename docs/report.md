# RiskPulse report notes

## Deliverable interpretation

The submission guidelines require a working public repository, a 5–7 slide PDF/PPTX, and a 10-minute unlisted demo video. They do **not** require a separate report PDF. The existing PDF is the presentation deck, not a technical report. Use this file as the written source of truth for the deck, pitch, and Q&A.

## Problem being solved

Risk teams receive more public financial news than they can manually triage. RiskPulse turns those headlines into event signals and maps high-severity events to portfolio exposures so an analyst can prioritize review and explain the result position by position.

## End-to-end method

1. Read bundled sample data, an uploaded CSV, or public Google News/GDELT feeds.
2. Normalize article fields and deduplicate by URL.
3. Classify sentiment and event type, identify known entities, and assign an impact score from 1 to 10.
4. Trigger a scenario only at impact 7 or above.
5. Apply event-specific equity, rate, spread, and credit shocks to each portfolio position.
6. Display portfolio totals, position losses, credit-loss increments, source articles, and matching news.

## Assumptions to state

- The portfolio is synthetic and is not a real person's, client's, or institution's portfolio.
- Scenario shocks are illustrative assumptions for a demonstration.
- The impact score is a ranking/triage proxy, not a causal forecast or guaranteed loss.
- The public benchmark has imperfect automatic ticker assignments.
- A live feed can be incomplete or rate limited, so the app uses the sources that respond.
- A 7+ score is a product rule chosen for the demo, not a regulatory threshold.
- The small holdout improvement over a median baseline is experimental and requires later-period and ticker-group validation.

## What remains before submission

- Replace the placeholder demo link and confirm public repository access.
- Verify the candidate/campus metadata and final deck link.
- Record and privately verify the 10-minute walkthrough.
- Re-run the validation commands from a clean machine or documented fresh environment.
- Submit the three links through the official form before the deadline.

## If a separate PDF report is later requested

The current rules do not specify a report page limit or report requirements, so do not invent one. Ask the organizer for the page limit, citation format, and required sections before producing a LaTeX report. The deck requirements are documented in [presentation_readme.md](presentation_readme.md).
