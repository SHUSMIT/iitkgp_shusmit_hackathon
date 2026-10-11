import pandas as pd

from src.ingestion.relevance import build_queries, filter_relevant, score_article
from src.stress.model import load_portfolio
from src.config import DATA_DIR

PORTFOLIO = load_portfolio(str(DATA_DIR / 'portfolio.csv'))


def test_queries_are_built_from_holdings():
    queries = build_queries(PORTFOLIO)
    joined = ' '.join(queries['rss'] + queries['gdelt'])
    for name in ['Microsoft', 'Walmart', 'Prologis', 'Chevron', 'Oracle']:
        assert name in joined
    assert all(len(q) < 480 for q in queries['rss'] + queries['gdelt'])


def test_holding_match_links_assets():
    result = score_article('Chevron raises capex as oil prices climb', '', PORTFOLIO)
    assert result['relevance'] == 'holding'
    assert 'Chevron' in result['matched_holdings']
    assert result['linked_assets']


def test_alias_and_ticker_match():
    assert score_article('Google unveils new cloud chip', '', PORTFOLIO)['relevance'] == 'holding'
    assert score_article('Shares of the lender (JPM) slide', '', PORTFOLIO)['relevance'] == 'holding'


def test_sector_and_macro_tiers():
    assert score_article('OPEC agrees surprise crude output cut', '', PORTFOLIO)['relevance'] == 'sector'
    assert score_article('New sanctions rattle markets as investors weigh the impact', '', PORTFOLIO)['relevance'] == 'macro'
    assert score_article('Americans say inflation has put early retirement out of reach', '', PORTFOLIO)['relevance'] == 'none'
    assert score_article('Israeli settlers attack farmers in West Bank', '', PORTFOLIO)['relevance'] == 'none'


def test_unrelated_articles_are_dropped():
    rows = [
        {'title': 'Local football club wins the league title', 'summary': 'Fans celebrate in the city centre'},
        {'title': 'Celebrity chef opens a new restaurant', 'summary': ''},
        {'title': 'Microsoft signs a large cloud contract', 'summary': ''},
    ]
    kept = filter_relevant(rows, PORTFOLIO)
    assert [r['title'] for r in kept] == ['Microsoft signs a large cloud contract']


def test_ambiguous_names_need_company_context():
    assert score_article('Apple pie recipes for the autumn season', '', PORTFOLIO)['relevance'] == 'none'
    assert score_article('Apple shares fall after weak iPhone demand', '', PORTFOLIO)['relevance'] == 'holding'
    assert score_article('Oracle bone inscriptions found at dig site', '', PORTFOLIO)['relevance'] == 'none'


def test_title_match_outranks_summary_only_match():
    in_title = score_article('Walmart cuts guidance on weak demand', '', PORTFOLIO)
    in_summary = score_article('Retail outlook darkens', 'Analysts say Walmart may cut guidance', PORTFOLIO)
    assert in_title['relevance_score'] > in_summary['relevance_score'] > 0.6


def test_rss_queries_are_per_holding_with_recency():
    queries = build_queries(PORTFOLIO, hours=6)
    assert any('"Prologis"' in q and 'when:6h' in q for q in queries['rss'])
    assert len([q for q in queries['rss'] if 'Chevron' in q]) == 1


def test_live_workflow_keeps_only_portfolio_relevant_news(monkeypatch):
    from src.ingestion.sources import Article
    from src.services import workflow

    def article(i, title, summary=''):
        return Article(f'a{i}', '', 'google_news', 'Wire', title, summary, f'https://news.example/{i}', 'q')

    feed = [
        article(1, 'Chevron warns of weaker refining margins'),
        article(2, 'Celebrity couple announce engagement'),
        article(3, 'Football club signs new striker'),
        article(4, 'Walmart faces credit downgrade risk as debt rises'),
        article(5, 'New sanctions rattle markets as investors weigh impact'),
    ]
    monkeypatch.setattr(workflow, 'ingest_all', lambda *args, **kwargs: feed)
    result = workflow.run_workflow(source='live', use_pretrained=False)
    titles = [s['title'] for s in result['signals']]
    assert 'Celebrity couple announce engagement' not in titles
    assert 'Football club signs new striker' not in titles
    assert result['fetched_count'] == 5 and result['article_count'] == 3
    assert {'Chevron', 'Walmart'} <= set(result['holdings_covered'])
    assert all(s['linked_holdings'] for s in result['scenarios'])
