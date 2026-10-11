from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Sequence

import numpy as np

from src.config import EMBEDDING_MODEL, IMPACT_CALIBRATION_FILE, IMPACT_MODEL_FILE, SENTIMENT_MODEL
from src.models.fallback import lexical_sentiment

EVENT_PROTOTYPES = {
    'Geopolitical': 'war sanctions tariffs conflict military attack export controls geopolitical escalation country risk',
    'Macroeconomic': 'inflation interest rates central bank monetary policy recession GDP unemployment growth currency macroeconomy',
    'Credit Event': 'default bankruptcy credit downgrade missed payment debt restructuring liquidity solvency non-performing loan',
    'Merger/Acquisition': 'merger acquisition takeover buyout strategic combination deal offer purchase',
    'Product Launch': 'new product launch release rollout platform technology service sales demand adoption',
    'Regulatory/Legal': 'regulator investigation lawsuit court rule regulation compliance penalty fine antitrust legal action',
    'Earnings/Guidance': 'quarterly earnings revenue profit loss guidance forecast outlook results margin',
    'Market Liquidity': 'liquidity funding stress spread widening market depth volatility fire sale',
    'Operational/Cyber': 'cyberattack outage breach ransomware operational disruption technology failure incident',
    'Commodity/Supply Chain': 'oil gas commodity prices supply chain disruption shipping logistics shortage raw materials',
}

EVENT_BASE_RISK = {
    'Geopolitical': 0.85,
    'Macroeconomic': 0.80,
    'Credit Event': 0.95,
    'Merger/Acquisition': 0.55,
    'Product Launch': 0.35,
    'Regulatory/Legal': 0.70,
    'Earnings/Guidance': 0.60,
    'Market Liquidity': 0.88,
    'Operational/Cyber': 0.78,
    'Commodity/Supply Chain': 0.68,
    'Other': 0.25,
}

RISK_WORDS = set('default bankruptcy downgrade sanctions war attack conflict escalation crisis fraud lawsuit fine penalty outage breach ransomware cyberattack recession inflation contagion liquidity restructuring missed payment debt'.split())
URGENCY_WORDS = set('immediate urgent emergency halted suspended unexpectedly shock crisis breaking restructuring missed'.split())


@dataclass
class ModelBundle:
    sentiment_model: object | None = None
    sentiment_tokenizer: object | None = None
    embedding_model: object | None = None
    impact_model: object | None = None
    impact_calibration: dict | None = None
    mode: str = 'lexical'


class RiskInference:
    def __init__(self, load_heavy_models: bool = True):
        self.bundle = ModelBundle()
        self.prototype_matrix: np.ndarray | None = None
        self.prototype_labels: list[str] = list(EVENT_PROTOTYPES)
        self.entities = self._load_entities()
        if load_heavy_models:
            self._load_optional_models()
        self._load_impact_model()
        self._build_prototypes()

    @staticmethod
    def _load_entities() -> dict[str, str]:
        path = Path(__file__).resolve().parents[2] / 'data' / 'entity_universe.csv'
        if not path.exists():
            return {}
        import pandas as pd
        df = pd.read_csv(path)
        return {str(r['entity_name']).lower(): str(r['ticker']) for _, r in df.iterrows()}

    def _load_optional_models(self) -> None:
        errors: list[str] = []
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            import torch
            tokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL)
            model = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL)
            model.eval()
            self.bundle.sentiment_model = model
            self.bundle.sentiment_tokenizer = tokenizer
        except Exception as exc:
            self.bundle.sentiment_model = None
            self.bundle.sentiment_tokenizer = None
            errors.append(f'{SENTIMENT_MODEL}: {type(exc).__name__}: {exc}')

        try:
            from sentence_transformers import SentenceTransformer
            self.bundle.embedding_model = SentenceTransformer(
                EMBEDDING_MODEL,
                device='cpu',
                model_kwargs={'low_cpu_mem_usage': False},
            )
        except Exception as exc:
            self.bundle.embedding_model = None
            errors.append(f'{EMBEDDING_MODEL}: {type(exc).__name__}: {exc}')

        if errors:
            # Model downloads and Torch/Transformers versions are optional
            # runtime dependencies. Keyword and lexical inference remains
            # deterministic and is required for an offline demonstration.
            self.bundle.mode = 'lexical-fallback'
        else:
            self.bundle.mode = 'pretrained'

    def _load_impact_model(self) -> None:
        if not IMPACT_MODEL_FILE.exists() or not IMPACT_CALIBRATION_FILE.exists():
            return
        try:
            from xgboost import XGBRegressor
            model = XGBRegressor()
            model.load_model(str(IMPACT_MODEL_FILE))
            self.bundle.impact_model = model
            self.bundle.impact_calibration = json.loads(IMPACT_CALIBRATION_FILE.read_text(encoding='utf-8'))
            if self.bundle.embedding_model is not None:
                self.bundle.mode += '+xgboost-impact'
        except Exception:
            self.bundle.impact_model = None
            self.bundle.impact_calibration = None

    def _embed(self, texts: Sequence[str]) -> np.ndarray:
        if self.bundle.embedding_model is not None:
            arr = self.bundle.embedding_model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(arr, dtype=np.float32)
        return np.zeros((len(texts), 1), dtype=np.float32)

    def _build_prototypes(self) -> None:
        texts = [EVENT_PROTOTYPES[k] for k in self.prototype_labels]
        self.prototype_matrix = self._embed(texts)

    @staticmethod
    def _sentiment_from_probs(probs: np.ndarray, id2label: dict) -> tuple[float, str]:
        labels = {str(id2label[i]).lower(): float(probs[i]) for i in range(len(probs))}
        positive = labels.get('positive', labels.get('label_2', 0.0))
        negative = labels.get('negative', labels.get('label_0', 0.0))
        score = float(np.clip(positive - negative, -1.0, 1.0))
        label = 'positive' if score > 0.08 else 'negative' if score < -0.08 else 'neutral'
        return score, label

    def sentiment(self, text: str) -> tuple[float, str]:
        if self.bundle.sentiment_model is not None and self.bundle.sentiment_tokenizer is not None:
            try:
                import torch
                tok = self.bundle.sentiment_tokenizer(text[:3000], return_tensors='pt', truncation=True, max_length=256)
                with torch.no_grad():
                    logits = self.bundle.sentiment_model(**tok).logits
                probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()
                return self._sentiment_from_probs(probs, self.bundle.sentiment_model.config.id2label)
            except Exception:
                pass
        return lexical_sentiment(text)

    def sentiment_batch(self, texts: list[str]) -> list[tuple[float, str]]:
        if self.bundle.sentiment_model is not None and self.bundle.sentiment_tokenizer is not None and texts:
            try:
                import torch
                batch = self.bundle.sentiment_tokenizer(
                    [text[:3000] for text in texts], return_tensors='pt', truncation=True, padding=True, max_length=256
                )
                with torch.no_grad():
                    logits = self.bundle.sentiment_model(**batch).logits
                probabilities = torch.softmax(logits, dim=-1).cpu().numpy()
                labels = self.bundle.sentiment_model.config.id2label
                return [self._sentiment_from_probs(row, labels) for row in probabilities]
            except Exception:
                pass
        return [lexical_sentiment(text) for text in texts]

    def event_class(self, text: str, vector: np.ndarray | None = None) -> tuple[str, float]:
        # Exact domain terms make the offline path deterministic. Embedding
        # inference is used for paraphrases when the pretrained model is present.
        low = text.lower()
        keyword_map = {
            'Geopolitical': ['sanctions','war','conflict','military','tariffs','export controls'],
            'Macroeconomic': ['inflation','interest rates','central bank','recession','gdp','unemployment'],
            'Credit Event': ['default','bankruptcy','debt restructuring','missed payment','downgrade','liquidity squeeze'],
            'Merger/Acquisition': ['acquisition','merger','takeover','buyout','transaction'],
            'Product Launch': ['new product','launch','rollout','new platform','new service'],
            'Regulatory/Legal': ['regulator','investigation','lawsuit','court','antitrust','fine','penalty','compliance'],
            'Earnings/Guidance': ['earnings','revenue','profit','guidance','forecast','quarterly'],
            'Market Liquidity': ['liquidity','market depth','funding stress','fire sale','spread widening'],
            'Operational/Cyber': ['cyberattack','ransomware','data breach','outage','service disruption','operational disruption'],
            'Commodity/Supply Chain': ['oil','gas','commodity','supply chain','shipping','shortage','raw materials'],
        }
        hits = {label: sum(1 for term in terms if term in low) for label, terms in keyword_map.items()}
        best_label = max(hits, key=hits.get)
        best_hits = hits[best_label]
        if best_hits > 0:
            confidence = float(np.clip(0.55 + 0.12 * best_hits, 0.55, 0.91))
            if self.bundle.embedding_model is None:
                return best_label, confidence
            # If the semantic classifier is confident and disagrees strongly, allow it
            # to win; otherwise preserve the explicit domain evidence.
            vec = vector if vector is not None else self._embed([text])[0]
            sims = self.prototype_matrix @ vec
            sem_idx = int(np.argmax(sims))
            sem_label = self.prototype_labels[sem_idx]
            sem_conf = float(np.clip((float(sims[sem_idx]) + 1.0) / 2.0, 0.0, 1.0))
            if sem_label == best_label or sem_conf < 0.78 or best_hits >= 2:
                return best_label, confidence
            return sem_label, sem_conf

        if self.bundle.embedding_model is None:
            return 'Other', 0.0
        vec = vector if vector is not None else self._embed([text])[0]
        sims = self.prototype_matrix @ vec
        idx = int(np.argmax(sims))
        raw = float(sims[idx])
        confidence = float(np.clip((raw + 1.0) / 2.0, 0.0, 1.0))
        return self.prototype_labels[idx], confidence

    def entities_in(self, text: str) -> list[str]:
        low = text.lower()
        found = []
        for name, ticker in self.entities.items():
            if re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', low):
                found.append(ticker)
        return sorted(set(found))

    def impact(self, text: str, event: str, confidence: float, sentiment: float, vector: np.ndarray | None = None) -> float:
        """Use fitted historical market moves when artifacts exist; else use the rule-based score."""
        if self.bundle.impact_model is not None and self.bundle.embedding_model is not None and self.bundle.impact_calibration:
            features = vector if vector is not None else self._embed([text])[0]
            predicted_log_move = float(self.bundle.impact_model.predict(features.reshape(1, -1))[0])
            predicted_move = float(np.expm1(max(0.0, predicted_log_move)))
            low = float(self.bundle.impact_calibration['p10_abs_return_pct'])
            high = float(self.bundle.impact_calibration['p90_abs_return_pct'])
            return float(np.clip(1.0 + 9.0 * (predicted_move - low) / max(high - low, 1e-6), 1.0, 10.0))

        """Transparent rule-based severity score; not a learned market forecast."""
        words = re.findall(r"[a-zA-Z][a-zA-Z'-]{1,}", text.lower())
        risk_hits = min(float(sum(word in RISK_WORDS for word in words)), 3.0)
        urgency_hits = min(float(sum(word in URGENCY_WORDS for word in words)), 2.0)
        score = (
            1.0
            + 4.0 * EVENT_BASE_RISK[event]
            + 1.0 * confidence
            + 0.55 * risk_hits
            + 0.65 * urgency_hits
            + 0.45 * abs(sentiment)
        )
        return float(np.clip(score, 1.0, 10.0))

    def analyze_rows(self, rows: list[dict]) -> list[dict]:
        if not rows:
            return []
        texts = [f"{str(row.get('title') or '')}. {str(row.get('summary') or '')}".strip()[:3500] for row in rows]
        sentiments = self.sentiment_batch(texts)
        vectors = self._embed(texts) if self.bundle.embedding_model is not None else [None] * len(texts)
        outputs: list[dict] = []
        for row, text, (sent, sent_label), vector in zip(rows, texts, sentiments, vectors):
            event, conf = self.event_class(text, vector)
            ents = self.entities_in(text)
            impact = self.impact(text, event, conf, sent, vector)
            impact_value = round(float(impact), 2)
            outputs.append({
                **row,
                'entity': ','.join(ents) if ents else '',
                'sentiment': round(sent, 4),
                'sentiment_label': sent_label,
                'event_class': event,
                'event_confidence': round(conf, 4),
                'impact_score': impact_value,
                'triggered_stress': bool(impact_value >= 7.0),
                'model_mode': self.bundle.mode,
            })
        return outputs
