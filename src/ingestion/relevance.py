"""Portfolio-driven news retrieval and relevance scoring.

Queries are built from the holdings of the loaded portfolio, and every fetched
article is tagged with how it relates to that portfolio:

* holding - names a counterparty or issuer in the portfolio (score 1.0 and up)
* sector  - concerns a sector the portfolio is exposed to (score 0.6)
* macro   - a systemic theme that moves the whole book (score 0.4)
* none    - unrelated; dropped from live feeds
"""
from __future__ import annotations

import re
from typing import Any, Iterable

import pandas as pd

TIER_SCORE = {'holding': 1.0, 'sector': 0.6, 'macro': 0.4, 'none': 0.0}
TIER_ORDER = ['none', 'macro', 'sector', 'holding']

NAME_ALIASES = {
    'Alphabet': ['Alphabet', 'Google'],
    'Exxon Mobil': ['Exxon Mobil', 'ExxonMobil', 'Exxon'],
    'JPMorgan Chase': ['JPMorgan Chase', 'JPMorgan', 'JP Morgan'],
    'Bank of America': ['Bank of America', 'BofA'],
    'S&P 500': ['S&P 500'],
    'CME Group': ['CME Group'],
}

SECTOR_KEYWORDS = {
    'Energy': ['oil prices', 'crude oil', 'opec', 'natural gas prices', 'oil refinery', 'lng exports'],
    'Technology': ['semiconductor', 'chipmaker', 'cloud computing', 'ai chips', 'data center demand'],
    'Financials': ['bank earnings', 'bank stocks', 'banking regulator', 'capital requirements', 'bank failures', 'lenders'],
    'Commercial Banking': ['corporate lending', 'loan defaults', 'credit losses', 'commercial loans'],
    'Consumer': ['retail sales', 'consumer spending', 'consumer credit', 'credit card delinquencies'],
    'Real Estate': ['commercial real estate', 'reit', 'commercial property', 'warehouse demand'],
    'Industrials': ['industrial output', 'manufacturing output', 'supply chain disruption'],
    'Rates': ['interest rate', 'rate cut', 'rate hike', 'treasury yield', 'yield curve'],
    'Equity Index': ['stock market', 'equity markets', 'stocks selloff', 'us stocks'],
}

MACRO_KEYWORDS = [
    'federal reserve', 'central bank', 'interest rate', 'inflation', 'recession', 'sanctions',
    'tariff', 'sovereign default', 'banking crisis', 'credit crunch', 'liquidity crisis',
]

# A macro theme counts only when it appears in a market or economy context.
MARKET_CONTEXT = [
    'market', 'stocks', 'bond', 'yield', 'wall street', 'investor', 'economy', 'economic',
    'federal reserve', 'central bank', 'rate', 'banks', 'lending', 'credit', 'trade',
]


def _holding_names(portfolio: pd.DataFrame) -> list[str]:
    names: list[str] = []
    for value in portfolio.get('counterparty', pd.Series(dtype=str)).dropna().astype(str):
        value = value.strip()
        if value and value not in names:
            names.append(value)
    return names


def _aliases(name: str) -> list[str]:
    return NAME_ALIASES.get(name, [name])


def _sectors(portfolio: pd.DataFrame) -> list[str]:
    seen: list[str] = []
    for value in portfolio.get('sector', pd.Series(dtype=str)).dropna().astype(str):
        if value.strip() and value.strip() not in seen:
            seen.append(value.strip())
    return seen


def _quote(term: str) -> str:
    return '"' + term.replace('"', '') + '"'


def _when(hours: int) -> str:
    return f'when:{int(hours)}h' if hours <= 48 else f'when:{max(1, int(hours) // 24)}d'


def build_queries(portfolio: pd.DataFrame, extra: str | None = None, hours: int = 24) -> dict[str, list[str]]:
    """Return RSS and GDELT query lists driven by the portfolio's holdings.

    RSS gets one precise query per holding so that heavily covered names cannot crowd out
    smaller ones; GDELT gets one combined holdings query and one market-wide query.
    """
    when = _when(hours)
    names = _holding_names(portfolio)
    rss = []
    for name in names:
        aliases = _aliases(name)
        rss.append('(' + ' OR '.join(_quote(a) for a in aliases[:2]) + ') ' + when)
    gdelt = ['(' + ' OR '.join(_quote(_aliases(n)[0]) for n in names) + ')']
    sector_terms = []
    for sector in _sectors(portfolio):
        sector_terms.extend(_quote(k) for k in SECTOR_KEYWORDS.get(sector, [sector.lower()])[:2])
    macro_terms = [_quote(k) for k in MACRO_KEYWORDS[:6]]
    market = ' OR '.join(macro_terms + sector_terms[:6])
    rss.append('(' + market + ') ' + when)
    gdelt.append('(' + market + ')')
    if extra and extra.strip():
        rss.append(f'({extra.strip()}) {when}')
        gdelt.append(f'({extra.strip()})')
    return {'rss': rss, 'gdelt': gdelt}


# Names that are also ordinary words need company context before they count as a holding.
AMBIGUOUS = {'Apple', 'Oracle', 'Visa'}
COMPANY_CONTEXT = [
    'shares', 'stock', 'earnings', 'revenue', 'profit', 'ceo', 'inc', 'corp', 'nasdaq', 'nyse',
    'investor', 'analyst', 'quarter', 'iphone', 'cloud', 'bond', 'debt', 'loan', 'lawsuit', 'regulator',
]
NON_FINANCIAL_TERMS = [
    'booties', 'shoes', 'sneakers', 'dress', 'fashion', 'recipe', 'restaurant',
    'celebrity', 'football', 'soccer', 'concert', 'movie', 'album',
]


def _match_name(text: str, alias: str) -> bool:
    return re.search(r'(?<![A-Za-z])' + re.escape(alias) + r'(?![A-Za-z])', text) is not None


def _match_ticker(text: str, ticker: str) -> bool:
    return re.search(r'(?:\$|\(|:\s?)' + re.escape(ticker) + r'(?![A-Za-z])', text) is not None


def _name_hit(text: str, name: str) -> bool:
    if not name:
        return False
    hit = any(_match_name(text, alias) for alias in _aliases(name))
    if hit and name in AMBIGUOUS:
        lowered = text.lower()
        hit = any(re.search(r'(?<![a-z])' + re.escape(c) + r'(?![a-z])', lowered) for c in COMPANY_CONTEXT)
    if hit:
        lowered = text.lower()
        has_non_financial_context = any(
            re.search(r'(?<![a-z])' + re.escape(term) + r'(?![a-z])', lowered)
            for term in NON_FINANCIAL_TERMS
        )
        has_company_context = any(
            re.search(r'(?<![a-z])' + re.escape(term) + r'(?![a-z])', lowered)
            for term in COMPANY_CONTEXT
        )
        if has_non_financial_context and not has_company_context:
            hit = False
    return hit


def score_article(title: str, summary: str, portfolio: pd.DataFrame) -> dict[str, Any]:
    text = f'{title} {summary}'
    lowered = text.lower()
    matched_names: list[str] = []
    linked_assets: list[str] = []
    in_title = False
    for _, row in portfolio.iterrows():
        name = str(row.get('counterparty', '')).strip()
        ticker = str(row.get('ticker', '')).strip()
        hit = _name_hit(text, name) or (len(ticker) >= 3 and _match_ticker(text, ticker))
        if hit:
            if name and name not in matched_names:
                matched_names.append(name)
            asset_id = str(row.get('asset_id', '')).strip()
            if asset_id and asset_id not in linked_assets:
                linked_assets.append(asset_id)
            if _name_hit(title, name) or (len(ticker) >= 3 and _match_ticker(title, ticker)):
                in_title = True
    if matched_names:
        tier = 'holding'
        score = (1.0 if in_title else 0.8) + min(0.2, 0.05 * (len(matched_names) - 1))
    else:
        sector_hit = None
        for sector in _sectors(portfolio):
            for keyword in SECTOR_KEYWORDS.get(sector, [sector.lower()]):
                if re.search(r'(?<![a-z])' + re.escape(keyword) + r'(?![a-z])', lowered):
                    sector_hit = sector
                    break
            if sector_hit:
                break
        if sector_hit:
            tier, score = 'sector', TIER_SCORE['sector']
            for _, row in portfolio[portfolio['sector'].astype(str) == sector_hit].iterrows():
                linked_assets.append(str(row.get('asset_id', '')))
            matched_names = [sector_hit]
        elif any(k in lowered for k in MACRO_KEYWORDS) and any(c in lowered for c in MARKET_CONTEXT):
            tier, score = 'macro', TIER_SCORE['macro']
            matched_names = ['Market-wide']
        else:
            tier, score = 'none', 0.0
    return {
        'relevance': tier,
        'relevance_score': round(score, 2),
        'matched_holdings': ', '.join(matched_names),
        'linked_assets': ', '.join(linked_assets),
    }


def tag_articles(rows: Iterable[dict[str, Any]], portfolio: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        item = dict(row)
        item.update(score_article(str(item.get('title', '')), str(item.get('summary', '')), portfolio))
        out.append(item)
    return out


def filter_relevant(rows: Iterable[dict[str, Any]], portfolio: pd.DataFrame, minimum: str = 'macro') -> list[dict[str, Any]]:
    floor = TIER_ORDER.index(minimum)
    tagged = tag_articles(rows, portfolio)
    kept = [r for r in tagged if TIER_ORDER.index(r['relevance']) >= floor and r['relevance'] != 'none']
    return sorted(kept, key=lambda r: r['relevance_score'], reverse=True)
