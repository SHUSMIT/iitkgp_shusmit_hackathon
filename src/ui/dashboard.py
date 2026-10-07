from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_URL = os.getenv('RISKPULSE_API_URL', 'http://127.0.0.1:8000').rstrip('/')

st.set_page_config(page_title='RiskPulse | Portfolio Stress', page_icon='📉', layout='wide')
st.title('RiskPulse')
st.caption('Event driven portfolio stress testing · Module B prototype')


def backend_get(path: str) -> dict:
    response = requests.get(f'{API_URL}{path}', timeout=5)
    response.raise_for_status()
    return response.json()


def backend_post(path: str, payload: dict) -> dict:
    response = requests.post(f'{API_URL}{path}', json=payload, timeout=180)
    response.raise_for_status()
    return response.json()


with st.sidebar:
    st.header('Analysis setup')
    try:
        backend_get('/health')
        st.success('Analysis backend connected')
    except requests.RequestException:
        st.error('Backend unavailable. Start it with: uvicorn src.api.app:app --reload')

    source_label = st.radio('News input', ['Included demo', 'Fetch public feeds', 'Upload CSV'])
    news_upload = st.file_uploader('News CSV', type='csv', disabled=source_label != 'Upload CSV')
    with st.expander('Live feed settings', expanded=source_label == 'Fetch public feeds'):
        hours = st.slider('Look-back window (hours)', 1, 168, 24)
        max_records = st.slider('Maximum articles per source', 5, 100, 30, 5)
        rss_query = st.text_input('Google News query', 'banking OR inflation OR recession OR sanctions OR credit when:1d')
    portfolio_upload = st.file_uploader('Optional portfolio CSV', type='csv')
    use_pretrained = st.checkbox(
        'Use local FinBERT and MiniLM inference',
        value=True,
        help='Downloads pretrained models on first use if they are not cached. The analysis fails if they cannot be loaded.',
    )
    run_button = st.button('Run portfolio analysis', type='primary', use_container_width=True)

if run_button:
    source_map = {'Included demo': 'sample', 'Fetch public feeds': 'live', 'Upload CSV': 'upload'}
    payload: dict = {
        'source': source_map[source_label],
        'hours': hours,
        'max_records': max_records,
        'rss_query': rss_query,
        'use_pretrained': use_pretrained,
    }
    try:
        if source_label == 'Upload CSV':
            if news_upload is None:
                st.error('Choose a news CSV first.')
                st.stop()
            news_df = pd.read_csv(news_upload).fillna('')
            if len(news_df) > 2000:
                st.error('News upload is limited to 2,000 rows per run.')
                st.stop()
            payload['articles'] = news_df.to_dict(orient='records')
        if portfolio_upload is not None:
            portfolio_df = pd.read_csv(portfolio_upload).fillna('')
            if len(portfolio_df) > 5000:
                st.error('Portfolio upload is limited to 5,000 rows.')
                st.stop()
            payload['portfolio'] = portfolio_df.to_dict(orient='records')
        with st.spinner('Fetching, classifying, and stressing the selected portfolio…'):
            st.session_state['result'] = backend_post('/pipeline/run', payload)
    except requests.HTTPError as exc:
        try:
            detail = exc.response.json().get('detail', str(exc))
        except (AttributeError, ValueError):
            detail = str(exc)
        st.error(f'Analysis failed: {detail}')
    except (requests.RequestException, pd.errors.ParserError, ValueError) as exc:
        st.error(f'Could not complete analysis: {exc}')

result = st.session_state.get('result')
if result is None:
    st.info('Choose a news source and run an analysis. The bundled sample works offline.')
    st.stop()

signals = pd.DataFrame(result['signals'])
scenarios = pd.DataFrame(result['scenarios'])
if signals.empty:
    st.warning('The selected source returned no articles.')
    st.stop()

st.caption(f"Model path: **{result['model_mode']}** · {result['article_count']} articles · {result['portfolio_asset_count']} assets")
high_impact = int(signals['triggered_stress'].astype(bool).sum())
portfolio_before = float(scenarios['before_value'].max()) if not scenarios.empty else 0.0
triggered_impacts = scenarios.loc[scenarios['triggered'].astype(bool), 'loss_value'] if not scenarios.empty else pd.Series(dtype=float)
largest_net_impact = float(triggered_impacts.iloc[triggered_impacts.abs().argmax()]) if not triggered_impacts.empty else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric('Articles analyzed', f'{len(signals):,}')
k2.metric('High impact signals', f'{high_impact:,}')
k3.metric('Portfolio value', f'{portfolio_before:,.0f}')
k4.metric('Largest net impact', f'{largest_net_impact:,.0f}',
          help='Signed impact with the largest absolute value; positive is loss and negative is gain.')

left, right = st.columns([1.3, 1])
with left:
    st.subheader('News risk signals')
    display_columns = ['published_at', 'publisher', 'title', 'entity', 'sentiment_label', 'event_class', 'event_confidence', 'impact_score', 'triggered_stress']
    st.dataframe(signals[[c for c in display_columns if c in signals.columns]].sort_values('impact_score', ascending=False),
                 use_container_width=True, hide_index=True)
with right:
    st.subheader('Event mix')
    event_mix = signals['event_class'].value_counts().rename_axis('Event').reset_index(name='Articles')
    st.plotly_chart(px.bar(event_mix, x='Event', y='Articles'), use_container_width=True)
    st.plotly_chart(px.histogram(signals, x='impact_score', nbins=10, title='Event severity distribution'), use_container_width=True)

if not scenarios.empty:
    st.subheader('Portfolio scenarios')
    labels = [f"{row.event_class} · impact {row.impact_score:.2f}" for row in scenarios.itertuples()]
    selected_index = st.selectbox('Scenario', range(len(labels)), format_func=lambda i: labels[i])
    scenario = result['scenarios'][selected_index]
    a, b, c = st.columns(3)
    a.metric('Before', f"{scenario['before_value']:,.0f}")
    net_gain = float(scenario['loss_value']) < 0
    b.metric('After', f"{scenario['after_value']:,.0f}", delta=f"{-scenario['loss_pct']:.2f}%")
    st.caption(f"Net {'gain' if net_gain else 'loss'}: {abs(float(scenario['loss_value'])):,.0f}. Positive asset impact values are losses; negative values are gains.")
    c.metric('Stress applied', 'Yes' if scenario['triggered'] else 'No')
    st.caption(f"Selected article: {scenario['article_title']}")
    st.json(scenario['shocks'], expanded=False)
    asset_df = pd.DataFrame(scenario['assets'])
    asset_df['_abs_impact'] = asset_df['asset_loss'].abs()
    asset_df = asset_df.sort_values('_abs_impact', ascending=False).drop(columns='_abs_impact')
    st.plotly_chart(px.bar(asset_df, x='asset_id', y='asset_loss', color='asset_type', title='Net impact by position (positive = loss, negative = gain)'), use_container_width=True)
    st.dataframe(asset_df, use_container_width=True, hide_index=True)

signals_csv = signals.to_csv(index=False).encode('utf-8')
st.download_button('Download analyzed signals', signals_csv, 'riskpulse_signals.csv', 'text/csv')
st.caption('Scenario shocks are illustrative assumptions. The current severity score is not a validated loss forecast.')
