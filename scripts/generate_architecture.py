"""Regenerate docs/architecture.png (layered RiskPulse architecture)."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

OUT = Path(__file__).resolve().parents[1] / 'docs' / 'architecture.png'
W, H = 12.2, 12.55
TEAL, PURPLE, ORANGE, GREEN, BLUE = '#2A9DAA', '#7A6BC4', '#E0954A', '#4FA27A', '#3B7DC1'
INK, MUTED, EDGE, FILL, BAND, LINE = '#14253B', '#5F7186', '#C9D6E2', '#FFFFFF', '#F1F5F9', '#5B7C99'

fig = plt.figure(figsize=(W, H), dpi=200)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')


def band(x, y, w, h, label, vertical=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.12', fc=BAND, ec=EDGE, lw=1.1))
    if vertical:
        ax.text(x + 0.27, y + h / 2, label, fontsize=8.5, color=MUTED, fontweight='bold', va='center', ha='center', rotation=90)
    else:
        ax.text(x + 0.2, y + h - 0.22, label, fontsize=9.5, color=MUTED, fontweight='bold', va='center')


def box(x, y, w, h, title, sub, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.08', fc=FILL, ec=EDGE, lw=1.0, zorder=3))
    ax.add_patch(Rectangle((x, y + 0.07), 0.07, h - 0.14, fc=color, ec='none', zorder=4))
    ax.text(x + 0.2, y + h - 0.25, title, fontsize=10.5, color=INK, fontweight="bold", va="center", zorder=5)
    ax.text(x + 0.2, y + h - 0.5, sub, fontsize=8.8, color=MUTED, va='top', linespacing=1.35, zorder=5)
    return dict(x=x, y=y, w=w, h=h, cx=x + w / 2, top=y + h, bot=y)


def line(xs, ys, color=LINE, lw=1.6):
    ax.plot(xs, ys, color=color, lw=lw, solid_capstyle='round', zorder=6)


def head(x, y0, y1, color=LINE, lw=1.6):
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle='-|>', mutation_scale=13, lw=lw, color=color, zorder=6, shrinkA=0, shrinkB=0))


def fan_in(srcs, dst, ymid, dst_x=None):
    """Several boxes above feed one box below through a bus line."""
    dx = dst['cx'] if dst_x is None else dst_x
    xs = [s['cx'] for s in srcs] + [dx]
    for s in srcs:
        line([s['cx'], s['cx']], [s['bot'], ymid])
    line([min(xs), max(xs)], [ymid, ymid])
    head(dx, ymid, dst['top'])


def fan_out(src, dsts, ymid, src_x=None):
    sx = src['cx'] if src_x is None else src_x
    xs = [d['cx'] for d in dsts] + [sx]
    line([sx, sx], [src['bot'], ymid])
    line([min(xs), max(xs)], [ymid, ymid])
    for d in dsts:
        head(d['cx'], ymid, d['top'])


def side(a, b, color=LINE):
    ym = a['y'] + a['h'] / 2 - 0.12
    ax.add_patch(FancyArrowPatch((a['x'] + a['w'], ym), (b['x'], ym), arrowstyle='-|>', mutation_scale=13, lw=1.5, color=color, zorder=6, shrinkA=0, shrinkB=0))


ax.text(0.25, H - 0.4, 'RiskPulse  |  System Architecture', fontsize=18, color=INK, fontweight='bold', va='center')
ax.text(0.25, H - 0.8, 'Unstructured news to structured risk signals to portfolio stress results', fontsize=10.5, color=MUTED, va='center')

MX, MW = 0.25, 8.95
SX, SW = 9.5, 2.45
LH, GAP = 1.5, 0.45
top = H - 1.2
bots = [top - i * (LH + GAP) - LH for i in range(6)]
mids = [bots[i] - GAP / 2 for i in range(5)]  # bus heights below layer i


def layer(i, label, specs, colors):
    y = bots[i]
    band(MX, y, MW, LH, label, vertical=True)
    n, left, pad, gap = len(specs), 0.6, 0.2, 0.2
    bw = (MW - left - pad - (n - 1) * gap) / n
    return [box(MX + left + k * (bw + gap), y + 0.2, bw, LH - 0.4, t, s, colors[k]) for k, (t, s) in enumerate(specs)]


L1 = layer(0, '1  SOURCES', [
    ('Google News RSS', 'Query-driven headlines\nand summaries'),
    ('GDELT DOC 2.0', 'Global news metadata,\nrefreshed every 15 min'),
    ('NewsAPI (optional)', 'Key-based additional\nnews source'),
    ('CSV upload', 'News and portfolio\nfiles')], [TEAL] * 4)
L2 = layer(1, '2  INGESTION', [
    ('Schema normalisation', 'Common article record:\ntitle, summary, time, URL'),
    ('Deduplication', 'URL-level merge across\nsources, stable article IDs'),
    ('Text preparation', 'Title and summary joined,\nlength-bounded')], [TEAL] * 3)
L3 = layer(2, '3  NLP ENGINE', [
    ('Sentiment', 'FinBERT probabilities\nto a score in [-1, 1]'),
    ('Event classifier', 'Domain terms + MiniLM\nclass-description match'),
    ('Entity matcher', 'Company / ticker\nlookup in text'),
    ('Impact scorer', 'XGBoost on MiniLM\nembeddings, scaled 1-10')], [PURPLE, PURPLE, PURPLE, ORANGE])
_bw = L3[0]['w']
_y4 = bots[3] + 0.2
L4 = [box(L3[0]['x'], _y4, _bw, LH - 0.4, 'Structured signal', 'Sentiment, event class,\nimpact score, entities', BLUE),
      box(L3[1]['x'], _y4, _bw, LH - 0.4, 'Stress trigger gate', 'Impact of 7 or more\nstarts a scenario', BLUE),
      box(L3[2]['x'], _y4, 2 * _bw + 0.2, LH - 0.4, 'Monitored signals', 'Scores below 7 stay in the ranked signal list\nfor review; no stress run is triggered', BLUE)]
band(MX, bots[3], MW, LH, '4  SIGNALS', vertical=True)
L5 = layer(4, '5  MODULE B', [
    ('Portfolio loader', 'Validates value, beta,\nduration, PD, LGD'),
    ('Scenario selector', 'Top-impact event per class\nselects the shock vector'),
    ('Market shock engine', 'Equity beta, rate and\nspread-duration effects'),
    ('Credit loss engine', 'Incremental EL:\nnotional x dPD x LGD')], [GREEN] * 4)
L6 = layer(5, '6  DELIVERY', [
    ('FastAPI service', 'Analysis, stress-test and\nfull pipeline endpoints'),
    ('React dashboard', 'Signals, scenarios, charts,\nposition drill-down'),
    ('CSV export', 'Signals and position-level\nloss detail')], [BLUE] * 3)

fan_in(L1, L2[0], mids[0])
side(L2[0], L2[1]); side(L2[1], L2[2])
fan_out(L2[2], L3, mids[1])
fan_in(L3, L4[0], mids[2])
side(L4[0], L4[1]); side(L4[1], L4[2])
head(L5[1]['cx'], L4[1]['bot'], L5[1]['top'])
for a, b in zip(L5[:-1], L5[1:]):
    side(a, b)
fan_out(L5[3], L6, mids[4])

# offline model build (flows upward into the impact scorer)
band_y, band_top = bots[4], bots[2] + LH
band(SX, band_y, SW, band_top - band_y, 'OFFLINE MODEL BUILD')
sub = [('Model artifacts', 'Trained impact model +\ncalibration (p10 / p90)', ORANGE),
       ('XGBoost training', 'Time-ordered holdout\nvs median baseline', ORANGE),
       ('Kaggle GPU', 'Frozen MiniLM\nembeddings', TEAL),
       ('EDT benchmark', 'Public news + next-day\nprice moves', PURPLE)]
bh, gap = 0.95, 0.26
ob = []
y = band_top - 0.5 - bh
for t, s, c in sub:
    ob.append(box(SX + 0.15, y, SW - 0.3, bh, t, s, c))
    y -= bh + gap
for upper, lower in zip(ob[:-1], ob[1:]):
    head(upper['cx'], lower['top'], upper['bot'], lw=1.5)
imp = L3[3]
ya = ob[0]['y'] + ob[0]['h'] / 2 - 0.12
ax.add_patch(FancyArrowPatch((ob[0]['x'], ya), (imp['x'] + imp['w'], ya), arrowstyle='-|>', mutation_scale=13, lw=1.7, color=ORANGE, zorder=6, shrinkA=0, shrinkB=0))

# legend
lx, ly = SX + 0.15, bots[5] + LH - 0.35
ax.text(lx, ly + 0.2, 'LEGEND', fontsize=9, color=MUTED, fontweight='bold')
for k, (c, t) in enumerate([(TEAL, 'Ingestion / data'), (PURPLE, 'NLP inference'), (ORANGE, 'Learned impact model'), (GREEN, 'Stress engine'), (BLUE, 'Contract / delivery')]):
    ax.add_patch(Rectangle((lx, ly - 0.2 - k * 0.24), 0.15, 0.15, fc=c, ec='none'))
    ax.text(lx + 0.27, ly - 0.125 - k * 0.24, t, fontsize=8.8, color=INK, va='center')

fig.savefig(OUT, dpi=200, facecolor='white')
print('wrote', OUT)
