'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { Navbar } from '@/components/Navbar';
import { ArrowLeft, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts';

// ── Types ────────────────────────────────────────────────────────────────────
interface EtfCatalog {
  ticker: string; name: string; category: string; sub_category: string;
  benchmark: string; gics_sector: string; expense_ratio: number; inception_date: string;
}

interface EtfScore {
  ticker: string; date: string;
  momentum_1m: number; momentum_3m: number; momentum_6m: number; momentum_12m: number;
  sharpe_1y: number; volatility_1y: number; max_drawdown_1y: number;
  beta_vs_spy: number; corr_vs_spy: number; sortino_ratio: number;
  composite_score: number; rank_overall: number; rank_category: number;
}

interface PriceBar { date: string; open: number; high: number; low: number; close: number; volume: number; }

interface ScoreHistory {
  date: string; composite_score: number; rank_overall: number;
  momentum_1m: number; momentum_3m: number; momentum_6m: number; momentum_12m: number;
  sharpe_1y: number; volatility_1y: number;
}

interface Holding { rank: number; symbol: string; name: string; weight_pct: number; }

interface RelatedEtf {
  ticker: string; name: string; composite_score: number; rank_overall: number;
  momentum_1m: number; momentum_3m: number; expense_ratio: number;
}

// ── Helpers ──────────────────────────────────────────────────────────────────
const CATEGORY_LABELS: Record<string, string> = {
  sector: 'Sector', factor: 'Factor / Style', fixed_income: 'Fixed Income',
  international: 'International', commodity: 'Commodity', real_estate: 'Real Estate',
  thematic: 'Thematic', volatility: 'Volatility', multi_asset: 'Multi-Asset',
};

function fmtPct(v: number | null | undefined, dec = 1): string {
  if (v == null) return '—';
  return `${v >= 0 ? '+' : ''}${v.toFixed(dec)}%`;
}
function fmtNum(v: number | null | undefined, dec = 2): string {
  if (v == null) return '—';
  return v.toFixed(dec);
}
function scoreColor(s: number): string {
  if (s >= 75) return '#10b981';
  if (s >= 50) return '#60a5fa';
  if (s >= 25) return '#f59e0b';
  return '#f43f5e';
}
function retColor(v: number | null | undefined): string {
  if (v == null) return 'var(--text-secondary)';
  return v >= 0 ? '#10b981' : '#f43f5e';
}

function ScoreArc({ score }: { score: number }) {
  const color = scoreColor(score);
  const r = 36; const circ = 2 * Math.PI * r;
  const fill = (score / 100) * circ;
  return (
    <div className="relative flex items-center justify-center w-24 h-24">
      <svg width={96} height={96} viewBox="0 0 96 96" className="-rotate-90">
        <circle cx={48} cy={48} r={r} fill="none" stroke="var(--border-color)" strokeWidth={8} />
        <circle cx={48} cy={48} r={r} fill="none" stroke={color} strokeWidth={8}
          strokeDasharray={`${fill} ${circ}`} strokeLinecap="round" />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-xl font-bold font-mono" style={{ color }}>{score.toFixed(0)}</span>
        <span className="text-[10px] text-[var(--text-secondary)]">Score</span>
      </div>
    </div>
  );
}

function StatCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-3">
      <p className="text-[11px] text-[var(--text-secondary)] mb-1">{label}</p>
      <p className="text-lg font-bold font-mono" style={{ color: color || 'var(--text-main)' }}>{value}</p>
      {sub && <p className="text-[10px] text-[var(--text-secondary)] mt-0.5">{sub}</p>}
    </div>
  );
}

const TIMEFRAMES: { label: string; days: number }[] = [
  { label: '1M', days: 21 }, { label: '3M', days: 63 },
  { label: '6M', days: 126 }, { label: '1Y', days: 252 },
];

// Custom tooltip for price chart
function PriceTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  return (
    <div className="rounded border border-[var(--border-color)] bg-[var(--bg-main)] px-3 py-2 text-xs shadow-lg">
      <p className="font-mono text-[var(--text-secondary)] mb-1">{label}</p>
      <p className="font-mono text-[var(--text-main)]">Close: <span className="font-semibold">${d?.close?.toFixed(2)}</span></p>
      <p className="text-[var(--text-secondary)]">Vol: {d?.volume?.toLocaleString()}</p>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function EtfDetailPage() {
  const { ticker } = useParams<{ ticker: string }>();
  const router = useRouter();
  const [catalog, setCatalog] = useState<EtfCatalog | null>(null);
  const [score, setScore] = useState<EtfScore | null>(null);
  const [prices, setPrices] = useState<PriceBar[]>([]);
  const [history, setHistory] = useState<ScoreHistory[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [related, setRelated] = useState<RelatedEtf[]>([]);
  const [tfIdx, setTfIdx] = useState(3); // default 1Y
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ticker) return;
    const t = ticker.toUpperCase();
    setLoading(true);
    Promise.all([
      fetch(`/api/etfs/${t}`).then(r => r.json()),
      fetch(`/api/etfs/${t}/scores/history?limit=252`).then(r => r.json()),
      fetch(`/api/etfs/${t}/holdings`).then(r => r.json()).catch(() => []),
      fetch(`/api/etfs/${t}/related`).then(r => r.json()).catch(() => []),
    ]).then(([detail, hist, hold, rel]) => {
      setCatalog(detail.catalog);
      setScore(detail.score);
      setPrices((detail.prices || []).slice().sort((a: PriceBar, b: PriceBar) => a.date.localeCompare(b.date)));
      setHistory((hist || []).slice().reverse());
      setHoldings(hold || []);
      setRelated(rel || []);
    }).catch(console.error).finally(() => setLoading(false));
  }, [ticker]);

  const visiblePrices = prices.slice(-TIMEFRAMES[tfIdx].days);

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col bg-[var(--bg-main)]">
        <Navbar />
        <div className="flex-1 flex items-center justify-center text-[var(--text-secondary)] text-sm">Loading…</div>
      </div>
    );
  }

  if (!catalog) {
    return (
      <div className="flex min-h-screen flex-col bg-[var(--bg-main)]">
        <Navbar />
        <div className="flex-1 flex items-center justify-center text-[var(--text-secondary)] text-sm">ETF not found.</div>
      </div>
    );
  }

  const priceChange = visiblePrices.length >= 2
    ? ((visiblePrices.at(-1)!.close - visiblePrices[0].close) / visiblePrices[0].close * 100)
    : null;
  const priceColor = priceChange == null ? 'var(--text-secondary)' : priceChange >= 0 ? '#10b981' : '#f43f5e';
  const areaColor = priceChange != null && priceChange >= 0 ? '#10b981' : '#f43f5e';

  return (
    <div className="flex min-h-screen flex-col bg-[var(--bg-main)] text-[var(--text-main)]">
      <Navbar />
      <main className="flex-1 w-full px-4 py-6 sm:px-6 space-y-6">

        {/* ── Back + Header ── */}
        <div>
          <button onClick={() => router.back()}
            className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)] hover:text-[var(--text-main)] transition-colors mb-4">
            <ArrowLeft size={14} /> Back to ETF Analysis
          </button>

          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <ScoreArc score={score?.composite_score ?? 0} />
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold font-mono">{catalog.ticker}</h1>
                <span className="px-2 py-0.5 rounded text-[11px] bg-[var(--border-color)] text-[var(--text-secondary)]">
                  {CATEGORY_LABELS[catalog.category] ?? catalog.category}
                </span>
                {score && (
                  <span className="text-xs text-[var(--text-secondary)]">
                    Rank #{score.rank_overall} of 92 · #{score.rank_category} in {CATEGORY_LABELS[catalog.category]}
                  </span>
                )}
              </div>
              <p className="text-[var(--text-secondary)] text-sm mt-1">{catalog.name}</p>
              <div className="flex flex-wrap gap-3 mt-2 text-xs text-[var(--text-secondary)]">
                {catalog.benchmark && <span>Tracks: <span className="text-[var(--text-main)]">{catalog.benchmark}</span></span>}
                {catalog.expense_ratio != null && (
                  <span>Expense Ratio: <span className="text-[var(--text-main)] font-mono">{(catalog.expense_ratio * 100).toFixed(2)}%</span></span>
                )}
                {score?.date && <span>As of <span className="font-mono">{score.date}</span></span>}
              </div>
            </div>
            {priceChange != null && (
              <div className="text-right">
                <p className="text-3xl font-bold font-mono">${visiblePrices.at(-1)?.close.toFixed(2)}</p>
                <p className="text-sm font-mono mt-1" style={{ color: priceColor }}>
                  {priceChange >= 0 ? <TrendingUp size={14} className="inline mr-1" /> : <TrendingDown size={14} className="inline mr-1" />}
                  {fmtPct(priceChange)} ({TIMEFRAMES[tfIdx].label})
                </p>
              </div>
            )}
          </div>
        </div>

        {/* ── Stats Grid ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
          {[
            { label: '1M Return', value: fmtPct(score?.momentum_1m), color: retColor(score?.momentum_1m) },
            { label: '3M Return', value: fmtPct(score?.momentum_3m), color: retColor(score?.momentum_3m) },
            { label: '6M Return', value: fmtPct(score?.momentum_6m), color: retColor(score?.momentum_6m) },
            { label: '12M Return', value: fmtPct(score?.momentum_12m), color: retColor(score?.momentum_12m) },
            { label: 'Sharpe (1Y)', value: fmtNum(score?.sharpe_1y), sub: 'risk-adj return' },
            { label: 'Sortino (1Y)', value: fmtNum(score?.sortino_ratio), sub: 'downside adj' },
            { label: 'Volatility', value: score?.volatility_1y != null ? `${score.volatility_1y.toFixed(1)}%` : '—', sub: 'ann. 20d' },
            { label: 'Max Drawdown', value: score?.max_drawdown_1y != null ? `${score.max_drawdown_1y.toFixed(1)}%` : '—', color: score?.max_drawdown_1y != null ? '#f43f5e' : undefined, sub: '1Y peak-to-trough' },
          ].map(c => <StatCard key={c.label} {...c} />)}
        </div>

        {/* ── Price Chart + Risk Stats ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* Price Chart */}
          <div className="lg:col-span-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold">Price Chart</h2>
              <div className="flex gap-1">
                {TIMEFRAMES.map((tf, i) => (
                  <button key={tf.label} onClick={() => setTfIdx(i)}
                    className={`px-2 py-0.5 rounded text-xs transition-colors ${tfIdx === i ? 'bg-blue-600 text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-main)]'}`}>
                    {tf.label}
                  </button>
                ))}
              </div>
            </div>
            {visiblePrices.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={visiblePrices} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={areaColor} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={areaColor} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }}
                    tickFormatter={d => d.slice(5)} interval={Math.floor(visiblePrices.length / 5)} />
                  <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
                  <Tooltip content={<PriceTooltip />} />
                  <Area dataKey="close" stroke={areaColor} strokeWidth={1.5} fill="url(#priceGrad)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            ) : <p className="text-center text-[var(--text-secondary)] text-sm py-10">No price data</p>}
          </div>

          {/* Risk Profile */}
          <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-4">
            <h2 className="text-sm font-semibold mb-3">Risk Profile</h2>
            <div className="space-y-3">
              {[
                { label: 'Beta vs SPY', value: fmtNum(score?.beta_vs_spy), hint: score?.beta_vs_spy != null ? (score.beta_vs_spy > 1.2 ? 'High sensitivity' : score.beta_vs_spy < 0.8 ? 'Low sensitivity' : 'Market-like') : '' },
                { label: 'Correlation vs SPY', value: fmtNum(score?.corr_vs_spy), hint: score?.corr_vs_spy != null ? (score.corr_vs_spy > 0.8 ? 'Highly correlated' : score.corr_vs_spy > 0.5 ? 'Moderate' : 'Low correlation') : '' },
                { label: 'Sharpe Ratio', value: fmtNum(score?.sharpe_1y), hint: score?.sharpe_1y != null ? (score.sharpe_1y > 1.5 ? 'Strong' : score.sharpe_1y > 0.5 ? 'Acceptable' : 'Weak') : '' },
                { label: 'Sortino Ratio', value: fmtNum(score?.sortino_ratio), hint: score?.sortino_ratio != null ? (score.sortino_ratio > 1.5 ? 'Strong downside adj.' : 'Moderate') : '' },
                { label: 'Volatility (ann.)', value: score?.volatility_1y != null ? `${score.volatility_1y.toFixed(1)}%` : '—', hint: score?.volatility_1y != null ? (score.volatility_1y < 15 ? 'Low' : score.volatility_1y < 25 ? 'Moderate' : 'High') : '' },
                { label: 'Max Drawdown', value: score?.max_drawdown_1y != null ? `${score.max_drawdown_1y.toFixed(1)}%` : '—', hint: '1Y trailing' },
                { label: 'Expense Ratio', value: catalog.expense_ratio != null ? `${(catalog.expense_ratio * 100).toFixed(2)}%` : '—', hint: 'Annual' },
              ].map(item => (
                <div key={item.label} className="flex justify-between items-center">
                  <div>
                    <p className="text-xs text-[var(--text-secondary)]">{item.label}</p>
                    {item.hint && <p className="text-[10px] text-[var(--text-secondary)] opacity-60">{item.hint}</p>}
                  </div>
                  <span className="font-mono text-sm font-semibold">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Score History Chart ── */}
        <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold">Composite Score History</h2>
            <span className="text-xs text-[var(--text-secondary)]">Last {history.length} trading days</span>
          </div>
          {history.length > 0 ? (
            <ResponsiveContainer width="100%" height={140}>
              <LineChart data={history} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }}
                  tickFormatter={d => d.slice(5)} interval={Math.floor(history.length / 6)} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
                <Tooltip formatter={(v: any) => [v?.toFixed(1), 'Score']}
                  contentStyle={{ background: 'var(--bg-main)', border: '1px solid var(--border-color)', fontSize: 11 }} />
                <ReferenceLine y={50} stroke="var(--border-color)" strokeDasharray="4 4" />
                <Line dataKey="composite_score" stroke="#60a5fa" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-center text-[var(--text-secondary)] text-sm py-6">No history data</p>}
        </div>

        {/* ── Holdings + Related ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* Holdings */}
          <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-4">
            <h2 className="text-sm font-semibold mb-3">Top Holdings</h2>
            {holdings.length > 0 ? (
              <div className="space-y-1">
                {holdings.slice(0, 15).map(h => (
                  <div key={h.symbol} className="flex items-center gap-2 py-1.5 border-b border-[var(--border-color)] last:border-0">
                    <span className="text-[11px] text-[var(--text-secondary)] w-5 text-right">{h.rank}</span>
                    <span className="font-mono text-xs font-semibold w-12">{h.symbol}</span>
                    <span className="text-xs text-[var(--text-secondary)] flex-1 truncate">{h.name}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1 bg-[var(--border-color)] rounded-full overflow-hidden">
                        <div className="h-full rounded-full bg-blue-500"
                          style={{ width: `${Math.min(100, (h.weight_pct / (holdings[0]?.weight_pct || 1)) * 100)}%` }} />
                      </div>
                      <span className="font-mono text-xs w-12 text-right">{h.weight_pct?.toFixed(2)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-[var(--text-secondary)] text-sm">Holdings not yet loaded</p>
                <p className="text-[10px] text-[var(--text-secondary)] mt-1 opacity-60">Run the ETF holdings loader to populate</p>
              </div>
            )}
          </div>

          {/* Related ETFs */}
          <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-4">
            <h2 className="text-sm font-semibold mb-3">
              Related ETFs — {CATEGORY_LABELS[catalog.category] ?? catalog.category}
            </h2>
            {related.length > 0 ? (
              <div className="space-y-2">
                {related.map(r => {
                  const sc = r.composite_score ?? 0;
                  const col = scoreColor(sc);
                  return (
                    <Link key={r.ticker} href={`/etfs/${r.ticker}`}
                      className="flex items-center gap-3 p-2 rounded-lg hover:bg-[var(--bg-main)] transition-colors cursor-pointer">
                      <div className="w-10 text-center">
                        <span className="font-mono text-xs font-bold">{r.ticker}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-[var(--text-secondary)] truncate">{r.name}</p>
                        <div className="mt-1 flex items-center gap-2">
                          <div className="flex-1 h-1 bg-[var(--border-color)] rounded-full overflow-hidden">
                            <div className="h-full rounded-full" style={{ width: `${sc}%`, backgroundColor: col }} />
                          </div>
                          <span className="text-[11px] font-mono" style={{ color: col }}>{sc.toFixed(0)}</span>
                        </div>
                      </div>
                      <div className="text-right text-[11px] font-mono">
                        <p style={{ color: retColor(r.momentum_1m) }}>{fmtPct(r.momentum_1m)}</p>
                        <p className="text-[var(--text-secondary)]">1M</p>
                      </div>
                    </Link>
                  );
                })}
              </div>
            ) : <p className="text-center text-[var(--text-secondary)] text-sm py-8">No related ETFs found</p>}
          </div>
        </div>

      </main>
    </div>
  );
}
