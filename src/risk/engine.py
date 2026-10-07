from __future__ import annotations
from pathlib import Path
import pandas as pd

from src.models.inference import RiskInference


def load_articles(path: str | Path) -> list[dict]:
    df = pd.read_csv(path)
    required = ['article_id', 'published_at', 'source', 'publisher', 'title', 'summary', 'url', 'query']
    for col in required:
        if col not in df.columns:
            df[col] = ''
    return df[required].fillna('').to_dict('records')


def analyze_file(input_csv: str | Path, output_csv: str | Path, heavy_models: bool = True) -> pd.DataFrame:
    rows = load_articles(input_csv)
    engine = RiskInference(load_heavy_models=heavy_models)
    result = pd.DataFrame(engine.analyze_rows(rows))
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_csv, index=False)
    return result
