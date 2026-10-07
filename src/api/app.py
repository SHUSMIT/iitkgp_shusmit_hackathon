from __future__ import annotations

from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.config import DATA_DIR
from src.services.workflow import analyze_articles, run_workflow, stress_portfolio
from src.services.llm import answer_news_question
from src.stress.model import load_portfolio

app = FastAPI(
    title='RiskPulse Event Stress API',
    description='News analysis and transparent event-driven portfolio scenarios.',
    version='2.0.0',
)


class PipelineRequest(BaseModel):
    source: Literal['sample', 'live', 'upload'] = 'sample'
    articles: list[dict[str, Any]] | None = Field(default=None, max_length=2000)
    portfolio: list[dict[str, Any]] | None = Field(default=None, max_length=5000)
    hours: int = Field(default=24, ge=1, le=168)
    max_records: int = Field(default=30, ge=1, le=100)
    gdelt_query: str = Field(default='', max_length=500)
    rss_query: str = Field(default='', max_length=300)
    use_pretrained: bool = True


class AnalyzeRequest(BaseModel):
    articles: list[dict[str, Any]] = Field(min_length=1, max_length=2000)
    use_pretrained: bool = True


class StressRequest(BaseModel):
    event_class: str = Field(min_length=1, max_length=64)
    impact_score: float = Field(ge=1, le=10)
    portfolio: list[dict[str, Any]] | None = Field(default=None, max_length=5000)


class LLMChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    signals: list[dict[str, Any]] = Field(default_factory=list, max_length=2000)
    asset: dict[str, Any] | None = None


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok', 'service': 'riskpulse-api'}


@app.get('/portfolio')
def portfolio() -> dict[str, Any]:
    try:
        rows = load_portfolio(str(DATA_DIR / 'portfolio.csv'))
        return {'count': len(rows), 'assets': rows.to_dict(orient='records')}
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post('/analyze')
def analyze(req: AnalyzeRequest) -> dict[str, Any]:
    try:
        result = analyze_articles(req.articles, req.use_pretrained)
        mode = str(result['model_mode'].iloc[0]) if not result.empty else 'unknown'
        return {'count': len(result), 'model_mode': mode, 'signals': result.to_dict(orient='records')}
    except (ValueError, RuntimeError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post('/stress-test')
def stress(req: StressRequest) -> dict[str, Any]:
    try:
        return stress_portfolio(req.event_class, req.impact_score, req.portfolio)
    except (ValueError, RuntimeError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post('/llm/chat')
def llm_chat(req: LLMChatRequest) -> dict[str, str]:
    try:
        return {'answer': answer_news_question(req.question, req.signals, req.asset)}
    except (ValueError, RuntimeError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post('/pipeline/run')
def pipeline(req: PipelineRequest) -> dict[str, Any]:
    try:
        return run_workflow(
            source=req.source,
            articles=req.articles,
            portfolio_rows=req.portfolio,
            hours=req.hours,
            max_records=req.max_records,
            gdelt_query=req.gdelt_query or None,
            rss_query=req.rss_query or None,
            use_pretrained=req.use_pretrained,
        )
    except (ValueError, RuntimeError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
