from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd

from src.config import DATA_DIR, DEFAULT_GDELT_QUERY, DEFAULT_RSS_QUERY
from src.ingestion.relevance import build_queries, filter_relevant, tag_articles
from src.ingestion.sources import ingest_all
from src.models.inference import RiskInference
from src.stress.model import StressResult, load_portfolio, run_stress, validate_portfolio

ARTICLE_COLUMNS = ['article_id', 'published_at', 'source', 'publisher', 'title', 'summary', 'url', 'query']


@lru_cache(maxsize=2)
def _engine(use_pretrained: bool) -> RiskInference:
    return RiskInference(load_heavy_models=use_pretrained)


def analyze_articles(rows: list[dict[str, Any]], use_pretrained: bool = True) -> pd.DataFrame:
    if not rows:
        raise ValueError('No news articles were supplied')
    normalized = []
    for row in rows:
        item = dict(row)
        for column in ARTICLE_COLUMNS:
            item.setdefault(column, '')
        normalized.append(item)
    return pd.DataFrame(_engine(use_pretrained).analyze_rows(normalized))


def serialize_stress(result: StressResult) -> dict[str, Any]:
    return {
        'event_class': result.event_class,
        'impact_score': result.impact_score,
        'triggered': result.triggered,
        'before_value': result.before_value,
        'after_value': result.after_value,
        'loss_value': result.loss_value,
        'loss_pct': result.loss_pct,
        'shocks': result.shocks,
        'assets': result.asset_table.to_dict(orient='records'),
    }


def stress_portfolio(event_class: str, impact_score: float, portfolio_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    portfolio = (
        validate_portfolio(pd.DataFrame(portfolio_rows))
        if portfolio_rows is not None
        else load_portfolio(str(DATA_DIR / 'portfolio.csv'))
    )
    return serialize_stress(run_stress(portfolio, event_class, impact_score))


def run_workflow(
    source: str = 'sample',
    articles: list[dict[str, Any]] | None = None,
    portfolio_rows: list[dict[str, Any]] | None = None,
    hours: int = 24,
    max_records: int = 30,
    gdelt_query: str | None = None,
    rss_query: str | None = None,
    use_pretrained: bool = True,
) -> dict[str, Any]:
    portfolio = (
        validate_portfolio(pd.DataFrame(portfolio_rows))
        if portfolio_rows is not None
        else load_portfolio(str(DATA_DIR / 'portfolio.csv'))
    )
    if source == 'sample':
        news = tag_articles(pd.read_csv(DATA_DIR / 'sample_news.csv').fillna('').to_dict('records'), portfolio)
    elif source == 'live':
        queries = build_queries(portfolio, extra=rss_query or gdelt_query, hours=hours)
        per_query = max(5, -(-max_records // 3))
        fetched = ingest_all(queries['gdelt'], queries['rss'], f'{hours}h', per_query)
        fetched_rows = [article.to_dict() for article in fetched]
        news = filter_relevant(fetched_rows, portfolio)
        fetched_count = len(fetched_rows)
        news = news[: max(max_records * 2, 20)]
        if not news:
            raise ValueError('No portfolio-relevant articles were found in the selected window. Try a longer lookback.')
    elif source == 'upload':
        news = tag_articles(articles or [], portfolio)
    else:
        raise ValueError('source must be sample, live, or upload')

    fetched_count = locals().get('fetched_count', len(news))
    signals = analyze_articles(news, use_pretrained)

    scenarios = []
    for event_class, group in signals.groupby('event_class', sort=False):
        candidate = group.sort_values(['relevance_score', 'impact_score', 'event_confidence'], ascending=False).iloc[0]
        result = serialize_stress(run_stress(portfolio, str(event_class), float(candidate['impact_score'])))
        scenarios.append({
            'event_class': result['event_class'],
            'article_title': str(candidate['title']),
            'linked_holdings': str(candidate.get('matched_holdings', '')),
            **result,
        })

    return {
        'model_mode': _engine(use_pretrained).bundle.mode,
        'article_count': len(signals),
        'fetched_count': fetched_count,
        'relevance_summary': signals['relevance'].value_counts().to_dict(),
        'holdings_covered': sorted({h.strip() for v in signals['matched_holdings'] for h in str(v).split(',') if h.strip() and h.strip() != 'Market-wide'}),
        'portfolio_asset_count': len(portfolio),
        'signals': signals.to_dict(orient='records'),
        'scenarios': scenarios,
    }
