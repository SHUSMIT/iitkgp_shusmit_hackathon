from pathlib import Path
from src.stress.model import load_portfolio, run_stress

ROOT = Path(__file__).resolve().parents[1]

def test_geopolitical_high_impact_triggers():
    pf = load_portfolio(str(ROOT/'data'/'portfolio.csv'))
    r = run_stress(pf, 'Geopolitical', 8.5)
    assert r.triggered
    assert r.after_value < r.before_value
    assert r.loss_value > 0

def test_low_impact_does_not_stress():
    pf = load_portfolio(str(ROOT/'data'/'portfolio.csv'))
    r = run_stress(pf, 'Geopolitical', 5.0)
    assert not r.triggered
    assert abs(r.before_value-r.after_value) < 1e-9
