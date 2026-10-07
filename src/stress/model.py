from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
import numpy as np

SHOCKS = {
    'Geopolitical': {'equity': -0.10, 'rate': 0.0075, 'spread': 0.0150, 'pd_mult': 1.35},
    'Macroeconomic': {'equity': -0.08, 'rate': 0.0200, 'spread': 0.0100, 'pd_mult': 1.30},
    'Credit Event': {'equity': -0.06, 'rate': 0.0100, 'spread': 0.0250, 'pd_mult': 2.00},
    'Merger/Acquisition': {'equity': 0.03, 'rate': -0.0025, 'spread': -0.0050, 'pd_mult': 0.95},
    'Product Launch': {'equity': 0.03, 'rate': 0.0000, 'spread': -0.0025, 'pd_mult': 0.98},
    'Regulatory/Legal': {'equity': -0.07, 'rate': 0.0050, 'spread': 0.0125, 'pd_mult': 1.25},
    'Earnings/Guidance': {'equity': -0.05, 'rate': 0.0025, 'spread': 0.0075, 'pd_mult': 1.15},
    'Market Liquidity': {'equity': -0.08, 'rate': 0.0075, 'spread': 0.0200, 'pd_mult': 1.50},
    'Operational/Cyber': {'equity': -0.05, 'rate': 0.0025, 'spread': 0.0100, 'pd_mult': 1.35},
    'Commodity/Supply Chain': {'equity': -0.06, 'rate': 0.0100, 'spread': 0.0125, 'pd_mult': 1.25},
    'Other': {'equity': 0.0, 'rate': 0.0, 'spread': 0.0, 'pd_mult': 1.0},
}


@dataclass
class StressResult:
    event_class: str
    impact_score: float
    triggered: bool
    before_value: float
    after_value: float
    loss_value: float
    loss_pct: float
    asset_table: pd.DataFrame
    shocks: dict


def load_portfolio(path: str) -> pd.DataFrame:
    return validate_portfolio(pd.read_csv(path))


def validate_portfolio(portfolio: pd.DataFrame) -> pd.DataFrame:
    df = portfolio.copy()
    required = {'asset_id', 'asset_type', 'current_value', 'notional', 'equity_beta', 'duration', 'spread_duration', 'pd', 'lgd'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'Portfolio missing required columns: {", ".join(sorted(missing))}')
    if df.empty:
        raise ValueError('Portfolio contains no assets')
    for column in ('asset_id', 'asset_type'):
        if df[column].isna().any() or df[column].astype(str).str.strip().eq('').any():
            raise ValueError(f'Portfolio column {column} cannot be empty')
    numeric = ['notional', 'current_value', 'equity_beta', 'duration', 'spread_duration', 'pd', 'lgd']
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors='coerce')
        if df[c].isna().any():
            raise ValueError(f'Portfolio column {c} contains missing or non-numeric values')
    if 'opening_value' not in df:
        df['opening_value'] = df['current_value']
    else:
        df['opening_value'] = pd.to_numeric(df['opening_value'], errors='coerce')
        if df['opening_value'].isna().any():
            raise ValueError('Portfolio column opening_value contains missing or non-numeric values')
    if 'closing_value' not in df:
        df['closing_value'] = df['current_value']
    else:
        df['closing_value'] = pd.to_numeric(df['closing_value'], errors='coerce')
        if df['closing_value'].isna().any():
            raise ValueError('Portfolio column closing_value contains missing or non-numeric values')
    if 'pnl' not in df:
        df['pnl'] = df['closing_value'] - df['opening_value']
    else:
        df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce')
        if df['pnl'].isna().any():
            raise ValueError('Portfolio column pnl contains missing or non-numeric values')
    if (df['current_value'] < 0).any() or (df['notional'] < 0).any():
        raise ValueError('Portfolio values and notionals must be non-negative')
    for c in ('pd', 'lgd'):
        if not df[c].between(0, 1).all():
            raise ValueError(f'Portfolio column {c} must be between 0 and 1')
    return df


def run_stress(portfolio: pd.DataFrame, event_class: str, impact_score: float) -> StressResult:
    if event_class not in SHOCKS:
        raise ValueError(f'Unknown event class: {event_class}')
    score = float(impact_score)
    if not np.isfinite(score) or not 1.0 <= score <= 10.0:
        raise ValueError('Impact score must be a finite value from 1 to 10')
    shock = SHOCKS[event_class].copy()
    triggered = score >= 7.0
    if not triggered:
        shock = {k: 0.0 if k != 'pd_mult' else 1.0 for k in shock}
    else:
        # Keep the scenario definition interpretable while letting severity scale
        # the shock continuously above the trigger threshold.
        severity_scale = score / 10.0
        shock = {k: (v * severity_scale if k != 'pd_mult' else 1.0 + (v - 1.0) * severity_scale) for k, v in shock.items()}

    out = portfolio.copy()
    out['market_return_shock'] = out['equity_beta'] * shock['equity']
    out['rate_impact'] = -out['duration'] * shock['rate']
    out['spread_impact'] = -out['spread_duration'] * shock['spread']
    out['price_factor'] = 1.0 + out['market_return_shock'] + out['rate_impact'] + out['spread_impact']
    out['market_shocked_value'] = out['current_value'] * out['price_factor']

    # Credit expected-loss shock for loan / credit-sensitive assets.
    credit_mask = out['asset_type'].str.lower().isin(['loan', 'bond', 'credit'])
    baseline_el = out['notional'] * out['pd'] * out['lgd']
    stressed_el = out['notional'] * np.clip(out['pd'] * shock['pd_mult'], 0, 0.95) * out['lgd']
    out['credit_loss_increment'] = np.where(credit_mask, np.maximum(0.0, stressed_el - baseline_el), 0.0)
    out['stressed_value'] = out['market_shocked_value'] - out['credit_loss_increment']
    out['asset_loss'] = out['current_value'] - out['stressed_value']
    out['asset_loss_pct'] = np.where(out['current_value'] != 0, out['asset_loss'] / out['current_value'] * 100.0, 0.0)

    before = float(out['current_value'].sum())
    after = float(out['stressed_value'].sum())
    loss = before - after
    loss_pct = (loss / before * 100.0) if before else 0.0

    return StressResult(
        event_class=event_class,
        impact_score=float(impact_score),
        triggered=triggered,
        before_value=before,
        after_value=after,
        loss_value=float(loss),
        loss_pct=float(loss_pct),
        asset_table=out,
        shocks=shock,
    )
