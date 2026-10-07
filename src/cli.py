from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

from src.pipeline import ingest_to_csv
from src.risk.engine import analyze_file
from src.stress.model import load_portfolio, run_stress
from src.config import DEFAULT_GDELT_QUERY, DEFAULT_RSS_QUERY


def main() -> None:
    parser = argparse.ArgumentParser(description='RiskPulse CLI')
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('ingest')
    p.add_argument('--hours', type=int, default=24)
    p.add_argument('--max-records', type=int, default=40)
    p.add_argument('--query', default=DEFAULT_GDELT_QUERY)
    p.add_argument('--rss-query', default=DEFAULT_RSS_QUERY)
    p.add_argument('--output', default='runtime/live_news.csv')

    p = sub.add_parser('analyze')
    p.add_argument('--input', required=True)
    p.add_argument('--output', default='runtime/signals.csv')
    p.add_argument('--fallback-only', action='store_true')

    p = sub.add_parser('stress-test')
    p.add_argument('--signals', required=True)
    p.add_argument('--portfolio', default='data/portfolio.csv')
    p.add_argument('--output', default='runtime/stress_test.csv')

    args = parser.parse_args()

    if args.command == 'ingest':
        df = ingest_to_csv(args.hours, args.max_records, args.query, args.rss_query, args.output)
        print(f'wrote {len(df)} articles to {args.output}')
        return

    if args.command == 'analyze':
        df = analyze_file(args.input, args.output, heavy_models=not args.fallback_only)
        print(f'wrote {len(df)} signals to {args.output}')
        if not df.empty:
            print(df[['source','title','sentiment','event_class','impact_score','triggered_stress']].head(10).to_string(index=False))
        return

    if args.command == 'stress-test':
        signals = pd.read_csv(args.signals)
        if signals.empty:
            raise SystemExit('No signals available')
        row = signals.sort_values(['impact_score','event_confidence'], ascending=False).iloc[0]
        portfolio = load_portfolio(args.portfolio)
        result = run_stress(portfolio, str(row['event_class']), float(row['impact_score']))
        result.asset_table.to_csv(args.output, index=False)
        print(f'event={result.event_class} impact={result.impact_score:.2f} triggered={result.triggered}')
        print(f'before={result.before_value:,.0f} after={result.after_value:,.0f} loss={result.loss_value:,.0f} ({result.loss_pct:.2f}%)')
        return


if __name__ == '__main__':
    main()
