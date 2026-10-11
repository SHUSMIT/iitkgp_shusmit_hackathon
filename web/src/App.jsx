import { useEffect, useMemo, useState } from 'react'
import Papa from 'papaparse'
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, BarChart3, Bell,
  BriefcaseBusiness, ChevronDown, CircleHelp, Clock3, Download, FileUp,
  Globe2, Layers3, RefreshCw, Search, ShieldCheck, SlidersHorizontal,
  Sparkles, Upload, Wifi, X, MessageCircle,
} from 'lucide-react'
import {
  Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts'

const API = '/api'
const palette = ['#54c7d8', '#8b9cff', '#efab65', '#ed7485', '#81c7a7', '#c58bef', '#f3d16d']
const money = (n) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(Number(n || 0))
const pct = (n) => `${Number(n || 0).toFixed(2)}%`
const portfolioColumns = ['asset_id', 'asset_type', 'current_value', 'notional', 'equity_beta', 'duration', 'spread_duration', 'pd', 'lgd']

function parseCsv(file) {
  return new Promise((resolve, reject) => Papa.parse(file, {
    header: true, skipEmptyLines: true, dynamicTyping: true,
    complete: ({ data, errors, meta }) => {
      if (errors.length) {
        reject(new Error(errors[0].message))
      } else if (!meta.fields?.length || !data.length) {
        reject(new Error('The selected CSV is empty or has no header row.'))
      } else {
        resolve(data)
      }
    },
    error: reject,
  }))
}

async function fetchJson(url, options = {}) {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), options.timeoutMs || 120000)
  try {
    const response = await fetch(url, { ...options, signal: controller.signal })
    const text = await response.text()
    let data
    try {
      data = text ? JSON.parse(text) : {}
    } catch {
      throw new Error(`The API returned an invalid response (HTTP ${response.status}).`)
    }
    if (!response.ok) throw new Error(data.detail || `The API request failed (HTTP ${response.status}).`)
    return data
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The analysis timed out after two minutes. Check that the API is running and try again.')
    throw error
  } finally {
    window.clearTimeout(timeout)
  }
}

function Metric({ icon: Icon, label, value, note, tone = 'blue' }) {
  return <article className="metric-card">
    <div className={`metric-icon ${tone}`}><Icon size={18} /></div>
    <div className="metric-copy"><span>{label}</span><strong>{value}</strong><small>{note}</small></div>
  </article>
}

function App() {
  const [source, setSource] = useState('sample')
  const [hours, setHours] = useState(24)
  const [limit, setLimit] = useState(30)
  const [newsFile, setNewsFile] = useState(null)
  const [portfolioFile, setPortfolioFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [apiOnline, setApiOnline] = useState(false)
  const [activeScenario, setActiveScenario] = useState(0)
  const [selectedSignal, setSelectedSignal] = useState(null)
  const [selectedAsset, setSelectedAsset] = useState(null)
  const [query, setQuery] = useState('banking OR inflation OR recession OR sanctions OR credit when:1d')
  const [search, setSearch] = useState('')
  const [chatQuestion, setChatQuestion] = useState('')
  const [chatAnswer, setChatAnswer] = useState('')
  const [chatLoading, setChatLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    let timer
    const checkHealth = async () => {
      try {
        await fetchJson(`${API}/health`, { timeoutMs: 5000 })
        if (!cancelled) setApiOnline(true)
      } catch {
        if (!cancelled) {
          setApiOnline(false)
          timer = window.setTimeout(checkHealth, 1500)
        }
      }
    }
    checkHealth()
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [])

  function scrollToSection(id) {
    const section = document.getElementById(id)
    if (section) {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } else {
      setError('Run an analysis first to populate this section.')
      document.getElementById('analysis-controls')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  async function runAnalysis() {
    setLoading(true); setError('')
    try {
      const payload = { source, hours: Number(hours), max_records: Number(limit), rss_query: query, use_pretrained: true }
      if (source === 'upload') {
        if (!newsFile) throw new Error('Choose a news CSV before running an upload analysis.')
        payload.articles = await parseCsv(newsFile)
      }
      if (portfolioFile) {
        payload.portfolio = await parseCsv(portfolioFile)
        const fields = Object.keys(payload.portfolio[0] || {})
        const missing = portfolioColumns.filter((column) => !fields.includes(column))
        if (missing.length) {
          throw new Error(`Portfolio CSV is missing required columns: ${missing.join(', ')}`)
        }
      } else {
        const portfolioData = await fetchJson(`${API}/portfolio`)
        payload.portfolio = portfolioData.assets
      }
      const data = await fetchJson(`${API}/pipeline/run`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
      })
      if (!data.signals?.length || !data.scenarios?.length) {
        throw new Error('The analysis completed without signals or portfolio scenarios.')
      }
      setResult(data)
      const firstTriggered = (data.scenarios || []).findIndex((item) => item.triggered)
      setActiveScenario(firstTriggered >= 0 ? firstTriggered : 0)
    } catch (e) {
      setError(e.message || 'Could not complete the analysis.')
    } finally { setLoading(false) }
  }

  const signals = result?.signals || []
  const scenarios = result?.scenarios || []
  const scenario = scenarios[Math.min(activeScenario, Math.max(0, scenarios.length - 1))]
  const visibleSignals = useMemo(() => {
    const q = search.trim().toLowerCase()
    return q ? signals.filter((s) => `${s.title} ${s.publisher} ${s.event_class} ${s.entity}`.toLowerCase().includes(q)) : signals
  }, [signals, search])
  const triggered = signals.filter((s) => s.triggered_stress).length
  const eventMix = useMemo(() => Object.entries(signals.reduce((a, s) => ({ ...a, [s.event_class]: (a[s.event_class] || 0) + 1 }), {})).map(([name, count]) => ({ name, count })), [signals])
  const assets = (scenario?.assets || []).slice().sort((a, b) => Math.abs(b.asset_loss) - Math.abs(a.asset_loss))
  const worstScenario = scenarios.filter((s) => s.triggered).reduce((best, item) =>
    !best || Math.abs(item.loss_value) > Math.abs(best.loss_value) ? item : best, null)
  const netGain = Number(scenario?.loss_value || 0) < 0
  const relatedSignals = selectedAsset ? signals.filter((signal) => {
    const haystack = `${signal.title} ${signal.summary} ${signal.entity} ${signal.event_class}`.toLowerCase()
    return [selectedAsset.asset_id, selectedAsset.counterparty, selectedAsset.sector, selectedAsset.ticker]
      .filter(Boolean)
      .some((term) => haystack.includes(String(term).toLowerCase()))
  }) : []

  function downloadSignals() {
    if (!signals.length) return
    const csv = Papa.unparse(signals)
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
    const a = document.createElement('a'); a.href = url; a.download = 'riskpulse_signals.csv'; a.click(); URL.revokeObjectURL(url)
  }

  async function askRiskAnalyst() {
    if (!chatQuestion.trim()) return
    setChatLoading(true); setChatAnswer('')
    try {
      const response = await fetch(`${API}/llm/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: chatQuestion, signals, asset: selectedAsset }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'The AI analyst request failed.')
      setChatAnswer(data.answer)
    } catch (e) { setChatAnswer(e.message || 'The AI analyst request failed.') }
    finally { setChatLoading(false) }
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Activity size={20} /></div><div><b>risk<span>pulse</span></b><small>PORTFOLIO INTELLIGENCE</small></div></div>
      <div className="workspace-label">WORKSPACE</div>
      <button className="side-link active" onClick={() => scrollToSection('analysis-controls')}><Layers3 size={17} /> Event stress <span className="side-dot" /></button>
      <button className="side-link" onClick={() => scrollToSection('signals')}><BarChart3 size={17} /> Risk signals</button>
      <button className="side-link" onClick={() => scrollToSection('portfolio')}><BriefcaseBusiness size={17} /> Portfolio impact</button>
      <div className="sidebar-bottom">
        <div className="source-status"><span className={`status-dot ${apiOnline ? 'online' : ''}`} /><div><b>{apiOnline ? 'API connected' : 'API offline'}</b><small>{apiOnline ? 'Risk engine ready' : 'Start FastAPI on :8000'}</small></div></div>
        <div className="sidebar-foot"><ShieldCheck size={14} /> Public and synthetic data only</div>
      </div>
    </aside>

    <main className="main-area">
      <header className="topbar"><div className="breadcrumb">Risk workspace <span>/</span> <b>Event stress</b></div><div className="top-actions"><span className="live-pill"><span /> LIVE MONITOR</span><button className="icon-button" aria-label="Help"><CircleHelp size={18} /></button><div className="avatar">RP</div></div></header>
      <section className="page-content">
        <div className="page-heading"><div><div className="eyebrow"><Sparkles size={13} /> MODULE B · EVENT-DRIVEN RISK</div><h1>Portfolio analysis</h1><p>Turn market-moving news into explainable portfolio scenarios.</p></div><button className="button secondary" onClick={downloadSignals} disabled={!signals.length}><Download size={16} /> Export signals</button></div>

        <section className="control-panel" id="analysis-controls">
          <div className="control-title"><div className="control-icon"><SlidersHorizontal size={17} /></div><div><b>Analysis controls</b><span>Choose data and run the risk engine</span></div></div>
          <div className="control-row">
            <label className="field"><span>NEWS SOURCE</span><div className="select-wrap"><Globe2 size={15} /><select value={source} onChange={(e) => setSource(e.target.value)}><option value="sample">Sample portfolio news</option><option value="live">Google News + GDELT feeds</option><option value="upload">Upload news CSV</option></select><ChevronDown size={15} /></div></label>
            {source === 'live' && <>
              <label className="field compact"><span>LOOKBACK</span><div className="select-wrap"><Clock3 size={15} /><select value={hours} onChange={(e) => setHours(e.target.value)}><option value="6">Last 6 hours</option><option value="24">Last 24 hours</option><option value="72">Last 3 days</option><option value="168">Last 7 days</option></select><ChevronDown size={15} /></div></label>
              <label className="field query-field"><span>NEWS QUERY</span><input value={query} onChange={(e) => setQuery(e.target.value)} /></label>
            </>}
            <label className="field compact"><span>MAX ARTICLES</span><div className="select-wrap"><Activity size={15} /><select value={limit} onChange={(e) => setLimit(e.target.value)}><option value="10">10 per source</option><option value="30">30 per source</option><option value="50">50 per source</option><option value="100">100 per source</option></select><ChevronDown size={15} /></div></label>
            {source === 'upload' && <label className="upload-chip"><Upload size={15} />{newsFile?.name || 'Choose news CSV'}<input type="file" accept=".csv,text/csv" onChange={(e) => setNewsFile(e.target.files?.[0] || null)} /></label>}
            <label className="upload-chip secondary-upload"><FileUp size={15} />{portfolioFile?.name || 'Portfolio CSV'}<input type="file" accept=".csv,text/csv" onChange={(e) => setPortfolioFile(e.target.files?.[0] || null)} /></label>
            <button className="button primary" onClick={runAnalysis} disabled={loading || !apiOnline}>{loading ? <><RefreshCw size={16} className="spin" /> Running analysis</> : <><Activity size={16} /> Run analysis</>}</button>
          </div>
          {error && <div className="error-banner"><AlertTriangle size={16} />{error}<button onClick={() => setError('')}><X size={15} /></button></div>}
        </section>
        <section className="explain-panel" aria-label="How the analysis works">
          <div className="explain-heading"><CircleHelp size={16} /><div><b>How to read this workspace</b><span>Decision support from public news to portfolio impact</span></div></div>
          <div className="explain-grid">
            <div><strong>What this solves</strong><p>Turns market-moving headlines into explainable event signals and shows which portfolio positions are most exposed.</p></div>
            <div><strong>What happens</strong><p>Headlines are normalized, scored for sentiment and event type, ranked from 1–10, then high-impact events are transmitted through beta, duration, spread, PD, and LGD.</p></div>
            <div><strong>Important assumptions</strong><p>A score of 7+ triggers a scenario. The portfolio and sample news are generated; live sources can return partial coverage; shocks are analyst-defined scenario assumptions, not forecasts or causal loss estimates.</p></div>
          </div>
        </section>

        {!result ? <section className="empty-state"><div className="empty-graphic"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="empty-core"><Activity size={30} /></div></div><h2>Your risk picture starts here</h2><p>Run the sample for an instant walkthrough, or connect to public feeds to scan current headlines.</p><button className="button primary" onClick={runAnalysis} disabled={loading || !apiOnline}><Sparkles size={16} /> Analyze sample portfolio</button></section> : <>
          <div className="result-meta"><div className="meta-right"><Wifi size={14} /> {result.article_count} articles <span /> <BriefcaseBusiness size={14} /> {result.portfolio_asset_count} portfolio positions <span /> Updated just now</div></div>

          <section className="metrics-grid">
            <Metric icon={Globe2} label="Articles analyzed" value={signals.length.toLocaleString()} note={source === 'live' ? 'Across available public feeds' : 'Source records processed'} tone="blue" />
            <Metric icon={AlertTriangle} label="High impact events" value={triggered.toLocaleString()} note="Impact score at or above 7" tone="amber" />
            <Metric icon={BriefcaseBusiness} label="Portfolio value" value={money(scenario?.before_value)} note={`${result.portfolio_asset_count} positions`} tone="purple" />
            <Metric icon={worstScenario?.loss_value < 0 ? ArrowUpRight : ArrowDownRight} label="Largest net impact" value={worstScenario ? money(worstScenario.loss_value) : money(0)} note="Largest absolute impact among triggered scenarios" tone={worstScenario?.loss_value < 0 ? 'blue' : 'red'} />
          </section>

          <section className="overview-grid">
            <article className="panel signals-panel" id="signals"><div className="panel-heading"><div><h2>Event risk signals</h2><p>Ranked by estimated event severity</p></div><div className="table-tools"><div className="search-box"><Search size={15} /><input placeholder="Search signals" value={search} onChange={(e) => setSearch(e.target.value)} /></div><button className="icon-button small" title="Refresh" onClick={runAnalysis}><RefreshCw size={15} /></button></div></div>
              <div className="signal-table-wrap"><table className="signal-table"><thead><tr><th>NEWS EVENT</th><th>EVENT TYPE</th><th>SENTIMENT</th><th>SEVERITY</th><th>STATUS</th></tr></thead><tbody>{visibleSignals.slice().sort((a, b) => b.impact_score - a.impact_score).map((s, i) => <tr className="clickable-row" onClick={() => setSelectedSignal(s)} key={s.article_id || `${s.title}-${i}`}><td><div className="event-title">{s.title}</div><div className="event-source">{s.publisher || s.source || 'Source unavailable'}{s.entity ? ` · ${s.entity}` : ''}</div></td><td><span className={`event-tag tag-${String(s.event_class).toLowerCase().replace(/[^a-z]+/g, '-')}`}>{s.event_class}</span></td><td><span className={`sentiment ${Number(s.sentiment) < -0.1 ? 'negative' : Number(s.sentiment) > 0.1 ? 'positive' : ''}`}>{Number(s.sentiment || 0) > 0 ? '+' : ''}{Number(s.sentiment || 0).toFixed(2)}</span></td><td><div className="severity-cell"><div className="severity-track"><i style={{ width: `${Number(s.impact_score) * 10}%` }} className={Number(s.impact_score) >= 7 ? 'hot' : ''} /></div><b>{Number(s.impact_score).toFixed(1)}</b></div></td><td><span className={`status-chip ${s.triggered_stress ? 'triggered' : 'watch'}`}>{s.triggered_stress ? 'Stress trigger' : 'Monitor'}</span></td></tr>)}</tbody></table>{visibleSignals.length === 0 && <div className="no-results">No signals match this search.</div>}</div>
              <div className="table-foot">Showing {Math.min(visibleSignals.length, 2000)} of {signals.length} signals <span>Impact scale: 1 low · 10 high</span></div>
            </article>
            <article className="panel mix-panel"><div className="panel-heading"><div><h2>Event composition</h2><p>Distribution across detected categories</p></div><button className="icon-button small" aria-label="More"><Bell size={15} /></button></div><div className="mix-chart"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={eventMix} dataKey="count" nameKey="name" innerRadius={63} outerRadius={89} paddingAngle={3} stroke="none">{eventMix.map((_, i) => <Cell key={i} fill={palette[i % palette.length]} />)}</Pie><Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #243347', background: '#101c2b', color: '#f4f7fb' }} /></PieChart></ResponsiveContainer><div className="mix-center"><strong>{signals.length}</strong><span>events</span></div></div><div className="legend-list">{eventMix.slice(0, 6).map((e, i) => <div key={e.name}><i style={{ background: palette[i % palette.length] }} /><span>{e.name}</span><b>{e.count}</b></div>)}</div></article>
          </section>

          <section className="panel portfolio-panel" id="portfolio"><div className="panel-heading"><div><div className="eyebrow"><BriefcaseBusiness size={13} /> PORTFOLIO TRANSMISSION</div><h2>Portfolio analysis</h2><p>Click a position for its sensitivities and related news</p></div><label className="scenario-select-label">STRESS SCENARIO<select value={activeScenario} onChange={(e) => setActiveScenario(Number(e.target.value))}>{scenarios.map((s, i) => <option key={`${s.event_class}-${i}`} value={i}>{s.event_class} · {Number(s.impact_score).toFixed(1)} severity</option>)}</select></label></div>
            {scenario ? <div className="portfolio-grid"><div className="loss-summary"><div className="loss-summary-top"><span className="summary-label">STRESSED PORTFOLIO VALUE</span><span className={`status-chip ${scenario.triggered ? 'triggered' : 'watch'}`}>{scenario.triggered ? 'Scenario triggered' : 'Below trigger'}</span></div><div className="portfolio-total">{money(scenario.after_value)}</div><div className="portfolio-before">from {money(scenario.before_value)} baseline value</div><div className="loss-divider" /><div className="loss-stats"><div><span>{netGain ? 'Net gain' : 'Net loss'}</span><b className={netGain ? '' : 'loss-red'}>{money(Math.abs(scenario.loss_value))}</b></div><div><span>Net portfolio impact</span><b className={netGain ? '' : 'loss-red'}>{pct(-scenario.loss_pct)}</b></div></div><div className="scenario-article"><span>SCENARIO DRIVER</span><p>{scenario.article_title}</p></div><div className="shock-tags">{Object.entries(scenario.shocks || {}).slice(0, 4).map(([k, v]) => <span key={k}>{k.replaceAll('_', ' ')} <b>{typeof v === 'number' ? v.toFixed(2) : v}</b></span>)}</div></div>
              <div className="asset-impact"><div className="asset-heading"><div><h3>Net impact by position</h3><p>Click a position for its sensitivities and related news</p></div><span>{assets.length} positions</span></div><div className="asset-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={assets.slice(0, 8)} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}><CartesianGrid stroke="#243347" horizontal={false} /><XAxis type="number" tickFormatter={(n) => `${(n / 1e6).toFixed(1)}m`} tick={{ fill: '#8291a4', fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis type="category" dataKey="asset_id" width={52} tick={{ fill: '#b8c4d2', fontSize: 11 }} axisLine={false} tickLine={false} /><Tooltip formatter={(v) => money(v)} contentStyle={{ borderRadius: 12, border: '1px solid #243347', background: '#101c2b', color: '#f4f7fb' }} /><Bar dataKey="asset_loss" radius={[0, 5, 5, 0]} barSize={16}>{assets.slice(0, 8).map((a, i) => <Cell key={a.asset_id} fill={a.asset_loss > 0 ? palette[(i + 2) % palette.length] : '#54c7d8'} />)}</Bar></BarChart></ResponsiveContainer></div><div className="asset-list">{assets.map((a) => <button className="asset-row" key={a.asset_id} onClick={() => setSelectedAsset(a)}><span><i className="asset-bullet" />{a.asset_id} <small>{a.asset_type}</small></span><b className={a.asset_loss > 0 ? 'loss-red' : ''}>{money(a.asset_loss)}</b></button>)}</div></div></div> : <div className="no-results">No portfolio scenarios were returned.</div>}
          </section>
          <section className="panel analyst-panel"><div className="panel-heading"><div><h2><MessageCircle size={17} /> AI risk analyst</h2><p>Ask about all analyzed news or the selected position.</p></div></div><div className="analyst-input"><input value={chatQuestion} onChange={(e) => setChatQuestion(e.target.value)} placeholder="What are the main risks across these news events?" onKeyDown={(e) => e.key === 'Enter' && askRiskAnalyst()} /><button className="button primary" onClick={askRiskAnalyst} disabled={chatLoading || !signals.length}>{chatLoading ? 'Analyzing…' : 'Ask Groq'}</button></div>{chatAnswer && <div className="analyst-answer">{chatAnswer}</div>}</section>
          <footer className="page-footer"><span>RISKPULSE · EVENT-DRIVEN PORTFOLIO STRESS TESTING</span><span><Clock3 size={13} /> Updated {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></footer>
        </>}
      </section>
    </main>
    {selectedSignal && <div className="detail-backdrop" onClick={() => setSelectedSignal(null)}><section className="detail-panel" onClick={(event) => event.stopPropagation()}><button className="detail-close" onClick={() => setSelectedSignal(null)}><X size={18} /></button><span className="eyebrow">AI NEWS ANALYSIS</span><h2>{selectedSignal.title}</h2><p className="detail-source">{selectedSignal.publisher || selectedSignal.source} · {selectedSignal.published_at || 'Publication time unavailable'}</p><p>{selectedSignal.summary || 'No article summary was provided by the source.'}</p><div className="detail-grid"><div><span>EVENT</span><b>{selectedSignal.event_class}</b></div><div><span>SENTIMENT</span><b>{selectedSignal.sentiment_label} ({Number(selectedSignal.sentiment).toFixed(2)})</b></div><div><span>IMPACT</span><b>{Number(selectedSignal.impact_score).toFixed(2)} / 10</b></div><div><span>CONFIDENCE</span><b>{(Number(selectedSignal.event_confidence) * 100).toFixed(0)}%</b></div></div><a className="article-link" href={selectedSignal.url} target="_blank" rel="noreferrer">Open full article <ArrowUpRight size={15} /></a></section></div>}
    {selectedAsset && <div className="detail-backdrop" onClick={() => setSelectedAsset(null)}><section className="detail-panel" onClick={(event) => event.stopPropagation()}><button className="detail-close" onClick={() => setSelectedAsset(null)}><X size={18} /></button><span className="eyebrow">POSITION ANALYSIS</span><h2>{selectedAsset.asset_id}{selectedAsset.ticker ? ` · ${selectedAsset.ticker}` : ''}</h2><p className="detail-source">{selectedAsset.asset_type} · {selectedAsset.sector} · {selectedAsset.counterparty}</p><div className="detail-grid"><div><span>OPENING VALUE</span><b>{money(selectedAsset.opening_value)}</b></div><div><span>CLOSING VALUE</span><b>{money(selectedAsset.closing_value)}</b></div><div><span>REALIZED P&L</span><b>{money(selectedAsset.pnl)}</b></div><div><span>SCENARIO LOSS</span><b>{money(selectedAsset.asset_loss)}</b></div><div><span>EQUITY BETA</span><b>{Number(selectedAsset.equity_beta).toFixed(2)}</b></div><div><span>DURATION</span><b>{Number(selectedAsset.duration).toFixed(2)}</b></div><div><span>SPREAD DURATION</span><b>{Number(selectedAsset.spread_duration).toFixed(2)}</b></div><div><span>CREDIT LOSS</span><b>{money(selectedAsset.credit_loss_increment)}</b></div></div><h3>Related analyzed news ({relatedSignals.length})</h3>{relatedSignals.length ? relatedSignals.map((signal) => <button className="related-news" key={signal.article_id} onClick={() => { setSelectedAsset(null); setSelectedSignal(signal) }}>{signal.title}<small>{signal.event_class} · impact {Number(signal.impact_score).toFixed(1)}</small></button>) : <p>No analyzed article matched this position's identifier, counterparty, or sector.</p>}</section></div>}
  </div>
}

export default App
