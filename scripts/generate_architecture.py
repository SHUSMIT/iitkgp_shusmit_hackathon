"""Regenerate docs/architecture.png from the current RiskPulse architecture."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 2200, 1120
image = Image.new('RGB', (WIDTH, HEIGHT), '#F4F7FA')
draw = ImageDraw.Draw(image)
font_dir = Path('C:/Windows/Fonts')


def font(name: str, size: int):
    path = font_dir / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


regular, small = font('segoeui.ttf', 23), font('segoeui.ttf', 18)
bold, title, eyebrow = font('seguisb.ttf', 25), font('seguisb.ttf', 42), font('seguisb.ttf', 17)
draw.text((70, 42), 'RiskPulse | Module B', font=title, fill='#13283A')
draw.text((72, 100), 'News ingestion, frozen text inference, CPU impact model, and transparent portfolio stress', font=regular, fill='#718298')

columns = [
    (60, 180, 290, 500, '01  PUBLIC INPUTS'),
    (400, 180, 280, 500, '02  INGESTION'),
    (730, 180, 390, 500, '03  EVENT INTELLIGENCE'),
    (1170, 180, 300, 500, '04  SIGNALS'),
    (1520, 180, 300, 500, '05  PORTFOLIO STRESS'),
    (1870, 180, 270, 500, '06  PRODUCT'),
]
for x, y, width, height, label in columns:
    draw.rounded_rectangle((x, y, x + width, y + height), radius=20, fill='#FFFFFF', outline='#DDE6ED', width=2)
    draw.text((x + 19, y + 19), label, font=eyebrow, fill='#7D91A4')


def card(x, y, width, height, heading, lines, accent='#54B9C8', fill='#FAFCFD'):
    draw.rounded_rectangle((x, y, x + width, y + height), radius=14, fill=fill, outline='#E1E9EF', width=2)
    draw.rounded_rectangle((x, y, x + 7, y + height), radius=4, fill=accent)
    draw.text((x + 22, y + 15), heading, font=bold, fill='#233C52')
    for i, line in enumerate(lines):
        draw.text((x + 22, y + 49 + i * 25), line, font=small, fill='#718298')


def arrow(x1, y1, x2, y2, color='#7596A7', width=4):
    import math

    draw.line((x1, y1, x2, y2), fill=color, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    length = 13
    p1 = (x2 - length * math.cos(angle - 0.5), y2 - length * math.sin(angle - 0.5))
    p2 = (x2 - length * math.cos(angle + 0.5), y2 - length * math.sin(angle + 0.5))
    draw.polygon([(x2, y2), p1, p2], fill=color)


card(82, 258, 245, 92, 'Google News RSS', ['Recent headlines; query driven'], '#59BEC9')
card(82, 377, 245, 92, 'GDELT DOC', ['News metadata; can rate-limit'], '#8195D5')
card(82, 496, 245, 92, 'CSV upload', ['News and portfolio inputs'], '#A888D2')
card(422, 330, 236, 130, 'Normalize + deduplicate', ['Source metadata and dates', 'Stable article IDs'], '#4CAEB7')
for y in (304, 423, 542):
    arrow(327, y, 422, 394)
card(752, 248, 345, 92, 'Frozen FinBERT (optional)', ['Sentiment inference; no fine-tuning'], '#8F80C7')
card(752, 365, 345, 92, 'Frozen MiniLM + prototypes', ['Event classification and embeddings'], '#4AA9BB')
card(752, 482, 345, 92, 'XGBoost CPU / rule fallback', ['Severity proxy, calibrated 1 to 10'], '#E6A269')
arrow(658, 395, 752, 294)
arrow(658, 395, 752, 411)
arrow(658, 395, 752, 528)
card(1192, 330, 256, 130, 'Structured event signals', ['Event, sentiment, severity', 'Entity, source, confidence'], '#4CAEB7')
arrow(1097, 294, 1192, 374)
arrow(1097, 411, 1192, 395)
arrow(1097, 528, 1192, 432)
card(1542, 268, 256, 92, 'Portfolio exposures', ['Synthetic sample or CSV upload'], '#8195D5')
card(1542, 407, 256, 110, 'Scenario stress engine', ['Equity beta / rate duration', 'Spread and credit shocks'], '#E6A269')
arrow(1448, 462, 1542, 462)
arrow(1670, 360, 1670, 407)
card(1892, 248, 226, 88, 'FastAPI service', ['Validation and workflow'], '#4E98BE')
card(1892, 366, 226, 88, 'React + Vite UI', ['Signals, scenarios, charts'], '#4E98BE')
card(1892, 484, 226, 88, 'CSV exports', ['Signals and loss detail'], '#7BAE94')
arrow(1798, 462, 1892, 292)
arrow(1798, 462, 1892, 410)
arrow(1798, 462, 1892, 528)

draw.rounded_rectangle((60, 748, 2140, 1047), radius=20, fill='#EDF3F7', outline='#D7E2EA', width=2)
draw.text((84, 766), 'OFFLINE MODEL BUILD | RUN ON KAGGLE WHEN RETRAINING', font=eyebrow, fill='#617B8F')
card(90, 817, 420, 116, 'Public EDT benchmark', ['News + next-day single-stock price labels', 'Large download; fetched on demand'], '#8296D1', '#F8FBFD')
card(670, 817, 420, 116, 'Kaggle GPU embeddings', ['Frozen MiniLM; resumable batches', 'Cache retained for reproducibility'], '#4AA9BB', '#F8FBFD')
card(1260, 817, 420, 116, 'CPU XGBoost training', ['Chronological holdout vs median baseline', 'Compact model + calibration artifacts'], '#E6A269', '#F8FBFD')
arrow(510, 875, 670, 875)
arrow(1090, 875, 1260, 875)
arrow(1470, 817, 920, 580, color='#D59B63', width=3)
draw.text((1510, 770), 'impact_xgb.json + calibration', font=small, fill='#9D754F')
draw.text((83, 1003), 'Prototype only | EDT labels are noisy | portfolio shocks are illustrative', font=small, fill='#77899A')

image.save('docs/architecture.png', optimize=True)
print(f'Wrote docs/architecture.png ({WIDTH}x{HEIGHT})')
