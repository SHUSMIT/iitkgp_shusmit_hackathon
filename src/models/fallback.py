from __future__ import annotations
import math
import re
from collections import Counter
import numpy as np

POSITIVE = set('beat beats bullish growth surge surged improve improved gain gains strong stronger rally rallies optimism optimistic upside expansion record records robust'.split())
NEGATIVE = set('loss losses bearish decline declined drop dropped weak weaker downgrade downgraded default defaults fraud scandal sanctions war layoffs recession bankruptcy liquidity crisis risk risks fall fallen negative downside contraction'.split())


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z'-]{1,}", text.lower())


def lexical_sentiment(text: str) -> tuple[float, str]:
    toks = tokenize(text)
    if not toks:
        return 0.0, 'neutral'
    counts = Counter(toks)
    pos = sum(counts[w] for w in POSITIVE)
    neg = sum(counts[w] for w in NEGATIVE)
    raw = (pos - neg) / max(1.0, math.sqrt(len(toks)))
    score = float(np.clip(raw / 4.0, -1.0, 1.0))
    if score > 0.12:
        label = 'positive'
    elif score < -0.12:
        label = 'negative'
    else:
        label = 'neutral'
    return score, label
