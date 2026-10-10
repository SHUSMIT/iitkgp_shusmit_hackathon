from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import html
import re
import warnings
from typing import Iterable
import xml.etree.ElementTree as ET

import requests

from src.config import GDELT_URL, GOOGLE_NEWS_RSS, NEWSAPI_KEY, NEWSAPI_URL


@dataclass
class Article:
    article_id: str
    published_at: str
    source: str
    publisher: str
    title: str
    summary: str
    url: str
    query: str

    def to_dict(self) -> dict:
        return asdict(self)


def _id(source: str, url: str, title: str) -> str:
    return hashlib.sha256(f'{source}|{url}|{title}'.encode('utf-8')).hexdigest()[:20]


def _clean(s: str | None) -> str:
    s = html.unescape(s or '')
    s = re.sub(r'<[^>]*>', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def fetch_gdelt(query: str, timespan: str = '24h', max_records: int = 50, timeout: int = 25) -> list[Article]:
    params = {
        'query': query,
        'mode': 'ArtList',
        'format': 'json',
        'maxrecords': max_records,
        'timespan': timespan,
        'sort': 'datedesc',
    }
    r = requests.get(
        GDELT_URL,
        params=params,
        timeout=timeout,
        headers={'User-Agent': 'RiskPulse-Hackathon/1.0'},
    )
    if r.status_code == 429:
        raise requests.HTTPError('GDELT rate limit reached; continuing with other sources.', response=r)
    r.raise_for_status()
    payload = r.json()
    out: list[Article] = []
    for item in payload.get('articles', []):
        title = _clean(item.get('title'))
        url = item.get('url') or item.get('sourceurl') or ''
        if not title or not url:
            continue
        published = item.get('seendate') or item.get('socialimage') or ''
        out.append(Article(
            article_id=_id('gdelt', url, title),
            published_at=str(published),
            source='gdelt',
            publisher=_clean(item.get('domain')),
            title=title,
            summary=_clean(item.get('snippet')),
            url=url,
            query=query,
        ))
    return out


def _parse_rss_time(value: str) -> str:
    return _clean(value)


def fetch_google_news_rss(query: str, max_records: int = 50, timeout: int = 25) -> list[Article]:
    params = {'q': query, 'hl': 'en-US', 'gl': 'US', 'ceid': 'US:en'}
    r = requests.get(GOOGLE_NEWS_RSS, params=params, timeout=timeout, headers={'User-Agent': 'RiskPulse-Hackathon/1.0'})
    r.raise_for_status()
    root = ET.fromstring(r.content)
    out: list[Article] = []
    for item in root.findall('./channel/item')[:max_records]:
        title = _clean(item.findtext('title'))
        url = _clean(item.findtext('link'))
        desc = _clean(item.findtext('description'))
        pub = _parse_rss_time(item.findtext('pubDate') or '')
        source = item.find('source')
        publisher = _clean(source.text if source is not None else 'Google News')
        if not title or not url:
            continue
        out.append(Article(
            article_id=_id('google_news', url, title),
            published_at=pub,
            source='google_news',
            publisher=publisher,
            title=title,
            summary=desc,
            url=url,
            query=query,
        ))
    return out


def fetch_newsapi(query: str, max_records: int = 50, timeout: int = 25) -> list[Article]:
    if not NEWSAPI_KEY:
        return []
    params = {
        'q': query,
        'language': 'en',
        'pageSize': min(max_records, 100),
        'sortBy': 'publishedAt',
        'apiKey': NEWSAPI_KEY,
    }
    r = requests.get(NEWSAPI_URL, params=params, timeout=timeout, headers={'User-Agent': 'RiskPulse-Hackathon/1.0'})
    r.raise_for_status()
    payload = r.json()
    if payload.get('status') != 'ok':
        raise RuntimeError(payload.get('message', 'NewsAPI error'))
    out: list[Article] = []
    for item in payload.get('articles', []):
        title = _clean(item.get('title'))
        url = item.get('url') or ''
        if not title or not url:
            continue
        publisher = _clean((item.get('source') or {}).get('name'))
        out.append(Article(
            article_id=_id('newsapi', url, title),
            published_at=_clean(item.get('publishedAt')),
            source='newsapi',
            publisher=publisher,
            title=title,
            summary=_clean(item.get('description')),
            url=url,
            query=query,
        ))
    return out


def dedupe(articles: Iterable[Article]) -> list[Article]:
    seen: set[str] = set()
    out: list[Article] = []
    for article in articles:
        key = (article.url or '').strip().lower() or article.article_id
        if key in seen:
            continue
        seen.add(key)
        out.append(article)
    return out


def ingest_all(query: str, rss_query: str, timespan: str, max_records: int) -> list[Article]:
    collected: list[Article] = []
    errors: list[str] = []
    for label, func, args in [
        ('gdelt', fetch_gdelt, {'query': query, 'timespan': timespan, 'max_records': max_records}),
        ('google_news', fetch_google_news_rss, {'query': rss_query, 'max_records': max_records}),
        ('newsapi', fetch_newsapi, {'query': query, 'max_records': max_records}),
    ]:
        try:
            collected.extend(func(**args))
        except Exception as exc:
            # One source failing must not make the full pipeline fail.
            status = getattr(getattr(exc, 'response', None), 'status_code', None)
            detail = f' HTTP {status}' if status else ''
            errors.append(f'{label}: {type(exc).__name__}{detail}')
    result = dedupe(collected)
    if not result and errors:
        raise RuntimeError('All live sources failed: ' + ' | '.join(errors))
    if result and errors:
        warnings.warn('Some live sources were unavailable: ' + ' | '.join(errors), RuntimeWarning)
    return result
