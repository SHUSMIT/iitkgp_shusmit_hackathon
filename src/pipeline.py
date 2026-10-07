from __future__ import annotations
from pathlib import Path
import pandas as pd

from src.config import DEFAULT_GDELT_QUERY, DEFAULT_RSS_QUERY, RUNTIME_DIR
from src.ingestion.sources import ingest_all


def ingest_to_csv(hours: int = 24, max_records: int = 40, query: str = DEFAULT_GDELT_QUERY, rss_query: str = DEFAULT_RSS_QUERY, output: str | None = None) -> pd.DataFrame:
    timespan = f'{hours}h'
    articles = ingest_all(query=query, rss_query=rss_query, timespan=timespan, max_records=max_records)
    df = pd.DataFrame([a.to_dict() for a in articles])
    if output is None:
        output = str(RUNTIME_DIR / 'live_news.csv')
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return df
