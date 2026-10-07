from __future__ import annotations

from typing import Any

import requests

from src.config import GROQ_API_KEY, GROQ_MODELS, GROQ_URL


def answer_news_question(
    question: str,
    signals: list[dict[str, Any]],
    asset: dict[str, Any] | None = None,
) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError('GROQ_API_KEY is not configured. Add it to .env and restart the API.')
    context = '\n'.join(
        f"- {item.get('title', '')} | event={item.get('event_class', '')} | "
        f"sentiment={item.get('sentiment_label', '')} | impact={item.get('impact_score', '')} | "
        f"summary={item.get('summary', '')}"
        for item in signals
    )
    asset_context = f'\nSelected position: {asset}\n' if asset else ''
    headers = {'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'}
    last_error = 'Groq returned no model response.'
    for model in GROQ_MODELS:
        payload = {
            'model': model,
            'temperature': 0.1,
            'messages': [
                {
                    'role': 'system',
                    'content': (
                        'You are RiskPulse, an event-driven portfolio risk analyst. '
                        'Reason only from the supplied analyzed news and position data. '
                        'Mention uncertainty and distinguish model signals from facts. '
                        'Answer concisely with drivers, affected exposures, and useful next checks.'
                    ),
                },
                {'role': 'user', 'content': f'Question: {question}\n{asset_context}\nAnalyzed news:\n{context}'},
            ],
        }
        response = requests.post(GROQ_URL, json=payload, timeout=45, headers=headers)
        if response.status_code == 429:
            last_error = f'Groq model {model} was rate limited.'
            continue
        if response.status_code >= 400:
            raise RuntimeError(f'Groq request failed with HTTP {response.status_code}: {response.text[:300]}')
        body = response.json()
        try:
            return str(body['choices'][0]['message']['content'])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError('Groq returned an unexpected response shape.') from exc
    raise RuntimeError(f'{last_error} All configured Groq models were unavailable.')
