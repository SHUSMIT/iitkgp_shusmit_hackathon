from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import EMBEDDING_MODEL


def _read_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == '.csv':
        return pd.read_csv(path).to_dict(orient='records')
    if path.suffix.lower() == '.jsonl':
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    payload = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(payload, dict):
        payload = payload.get('data', payload.get('articles', []))
    if not isinstance(payload, list):
        raise ValueError('Expected a JSON list of news records')
    return payload


def load_event_outcomes(path: str | Path) -> pd.DataFrame:
    """Normalize EDT-style forward-price labels or a prepared CSV to one schema."""
    rows = []
    for row in _read_records(Path(path)):
        labels = row.get('labels') or {}
        if isinstance(labels, str):
            try:
                labels = json.loads(labels)
            except json.JSONDecodeError:
                labels = {}
        labels = labels if isinstance(labels, dict) else {}
        title = str(row.get('title') or row.get('headline') or '').strip()
        body = str(row.get('text') or row.get('summary') or row.get('article') or '').strip()
        published = row.get('pub_time') or row.get('published_at') or row.get('date') or ''
        ticker = str(row.get('ticker') or labels.get('ticker') or row.get('stock') or '').strip()
        start = row.get('start_price_close') or labels.get('start_price_close') or labels.get('start_price_open')
        end = row.get('end_price_1day') or labels.get('end_price_1day')
        try:
            explicit_target = row.get('target_return_pct')
            target = abs(float(explicit_target)) if explicit_target not in (None, '') else abs((float(end) / float(start) - 1.0) * 100.0)
        except (TypeError, ValueError, ZeroDivisionError):
            continue
        if not title or not np.isfinite(target) or target < 0 or target > 100:
            continue
        rows.append({
            'published_at': published,
            'ticker': ticker,
            'title': title,
            'summary': body[:3000],
            'target_abs_return_pct': target,
        })

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError('No valid rows. Need title plus target_return_pct, or EDT start/end price labels.')
    frame['published_at'] = pd.to_datetime(frame['published_at'], errors='coerce', utc=True)
    frame = frame.dropna(subset=['published_at']).drop_duplicates(['published_at', 'ticker', 'title']).sort_values('published_at')
    return frame.reset_index(drop=True)


def train_impact_model(
    data_path: str | Path,
    output_dir: str | Path = 'models',
    max_rows: int = 50_000,
    batch_size: int = 128,
    device: str | None = None,
) -> dict[str, Any]:
    """Fit XGBoost on frozen MiniLM vectors and next-day absolute price moves."""
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from xgboost import XGBRegressor

    data = load_event_outcomes(data_path)
    if len(data) > max_rows:
        data = data.tail(max_rows).reset_index(drop=True)
    if len(data) < 500:
        raise ValueError(f'Need at least 500 usable historical event rows; found {len(data)}')

    selected_device = device or ('cuda' if __import__('torch').cuda.is_available() else 'cpu')
    encoder = SentenceTransformer(EMBEDDING_MODEL, device=selected_device)
    texts = (data['title'] + '. ' + data['summary']).tolist()
    embeddings = encoder.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    ).astype(np.float32)

    y = np.log1p(data['target_abs_return_pct'].to_numpy(dtype=np.float32))
    split = max(1, min(len(data) - 1, int(len(data) * 0.8)))
    if data['published_at'].notna().any():
        X_train, X_valid = embeddings[:split], embeddings[split:]
        y_train, y_valid = y[:split], y[split:]
        raw_valid = data['target_abs_return_pct'].to_numpy(dtype=np.float32)[split:]
    else:
        raise ValueError('Need valid publication timestamps for a time-ordered train/validation split')

    model = XGBRegressor(
        n_estimators=350,
        max_depth=5,
        learning_rate=0.04,
        subsample=0.85,
        colsample_bytree=0.8,
        reg_lambda=5.0,
        objective='reg:squarederror',
        tree_method='hist',
        device='cpu',
        n_jobs=4,
        random_state=20261003,
    )
    model.fit(X_train, y_train, eval_set=[(X_valid, y_valid)], verbose=False)
    predictions = np.expm1(np.maximum(0.0, model.predict(X_valid)))
    mae = float(mean_absolute_error(raw_valid, predictions))
    rmse = float(np.sqrt(mean_squared_error(raw_valid, predictions)))
    baseline = float(np.median(data['target_abs_return_pct'].to_numpy(dtype=np.float32)[:split]))
    baseline_mae = float(mean_absolute_error(raw_valid, np.full_like(raw_valid, baseline)))

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    model.save_model(output / 'impact_xgb.json')
    calibration = {
        'embedding_model': EMBEDDING_MODEL,
        'target': 'absolute next-trading-day price move in percent',
        'target_transform': 'log1p',
        'p10_abs_return_pct': float(data['target_abs_return_pct'].iloc[:split].quantile(0.10)),
        'p90_abs_return_pct': float(data['target_abs_return_pct'].iloc[:split].quantile(0.90)),
        'rows': len(data),
        'train_rows': split,
        'validation_rows': len(data) - split,
        'validation_mae_pct_points': mae,
        'validation_rmse_pct_points': rmse,
        'median_baseline_mae_pct_points': baseline_mae,
        'validation_period_start': str(data['published_at'].iloc[split]),
    }
    (output / 'impact_calibration.json').write_text(json.dumps(calibration, indent=2), encoding='utf-8')
    np.savez_compressed(
        output / 'embedding_cache.npz',
        embeddings=embeddings.astype(np.float16),
        target_abs_return_pct=data['target_abs_return_pct'].to_numpy(dtype=np.float32),
        published_at=data['published_at'].astype(str).to_numpy(),
    )
    return calibration
