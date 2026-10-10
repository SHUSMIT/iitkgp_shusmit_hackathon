"""Build docs/results.png: scenario results for Module B on data/portfolio.csv."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.stress.model import load_portfolio, run_stress

p = load_portfolio(str(ROOT / 'data' / 'portfolio.csv'))
events = ['Macroeconomic', 'Credit Event', 'Geopolitical', 'Market Liquidity', 'Regulatory/Legal', 'Operational/Cyber']
types = ['Loan', 'Bond', 'Derivative', 'Equity', 'Credit']
colors = ['#3B7DC1', '#2A9DAA', '#E0954A']
fig, axs = plt.subplots(1, 2, figsize=(11, 4.0), dpi=200)

ax = axs[0]
w = 0.26
for k, ev in enumerate(['Geopolitical', 'Macroeconomic', 'Credit Event']):
    t = run_stress(p, ev, 8.0).asset_table
    vals = [t[t.asset_type == a].asset_loss.sum() / 1e6 for a in types]
    ax.bar([i + (k - 1) * w for i in range(len(types))], vals, w, label=ev, color=colors[k])
ax.set_xticks(range(len(types))); ax.set_xticklabels(types)
ax.set_ylabel('Scenario loss (USD million)'); ax.set_title('Loss by asset type (severity 8)', fontsize=11, fontweight='bold')
ax.legend(frameon=False, fontsize=9); ax.spines[['top', 'right']].set_visible(False); ax.grid(axis='y', alpha=.25)

ax = axs[1]
scores = [7, 7.5, 8, 8.5, 9, 9.5, 10]
for ev, c in zip(events[:4], ['#3B7DC1', '#E0954A', '#2A9DAA', '#7A6BC4']):
    ax.plot(scores, [run_stress(p, ev, s).loss_pct for s in scores], marker='o', ms=4, lw=1.8, label=ev, color=c)
ax.set_xlabel('Impact score'); ax.set_ylabel('Portfolio loss (%)')
ax.set_title('Loss versus impact score (trigger at 7)', fontsize=11, fontweight='bold')
ax.legend(frameon=False, fontsize=9); ax.spines[['top', 'right']].set_visible(False); ax.grid(alpha=.25)
fig.tight_layout()
fig.savefig(ROOT / 'docs' / 'results.png', facecolor='white')
