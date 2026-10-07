from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd

from src.config import DATA_DIR, DEFAULT_GDELT_QUERY, DEFAULT_RSS_QUERY
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
    if source == 'sample':
        news = pd.read_csv(DATA_DIR / 'sample_news.csv').fillna('').to_dict('records')
    elif source == 'live':
        fetched = ingest_all(gdelt_query or DEFAULT_GDELT_QUERY, rss_query or DEFAULT_RSS_QUERY, f'{hours}h', max_records)
        news = [article.to_dict() for article in fetched]
    elif source == 'upload':
        news = articles or []
    else:
        raise ValueError('source must be sample, live, or upload')

    signals = analyze_articles(news, use_pretrained)
    portfolio = (
        validate_portfolio(pd.DataFrame(portfolio_rows))
        if portfolio_rows is not None
        else load_portfolio(str(DATA_DIR / 'portfolio.csv'))
    )

    scenarios = []
    for event_class, group in signals.groupby('event_class', sort=False):
        candidate = group.sort_values(['impact_score', 'event_confidence'], ascending=False).iloc[0]
        result = serialize_stress(run_stress(portfolio, str(event_class), float(candidate['impact_score'])))
        scenarios.append({
            'event_class': result['event_class'],
            'article_title': str(candidate['title']),
            **result,
        })

    return {
        'model_mode': _engine(use_pretrained).bundle.mode,
        'article_count': len(signals),
        'portfolio_asset_count': len(portfolio),
        'signals': signals.to_dict(orient='records'),
        'scenarios': scenarios,
    }
