'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { Navbar } from '@/components/Navbar';
import { ArrowLeft, ExternalLink, TrendingUp, TrendingDown, Layers, ShieldCheck, Activity } from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Cell,
  LineChart, Line,
} from 'recharts';

interface SectorDetail {
  id: number;
  symbol: string;
  name: string;
  gics_code?: string;
  description?: string;
  why?: string[];
  total_companies?: number;
  latest_score: {
    overall_score: number;
    rank: number;
    classification: string;
    rs_ratio?: number;
    rs_momentum?: number;
    scores?: {
      relative_strength: number;
      momentum: number;
      trend: number;
      regime_fit: number;
      risk: number;
      breadth_estimate?: number;
      fundamental?: number;
      surprise_estimate?: number;
    };
  };
  companies: Array<{
    id: number;
    ticker: string;
    company_name: string;
    exchange: string;
    industry?: string;
    market_cap_tier?: string;
  }>;
}

function retColor(v: number | null | undefined): string {
  if (v === null || v === undefined) return '#64748b';
  return v >= 0 ? '#10b981' : '#f43f5e';
}

function fmtReturn(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—';
  return `${v >= 0 ? '+' : ''}${(v * 100).toFixed(2)}%`;
}

const REGIME_COLORS: Record<string, string> = {
  Goldilocks: '#10b981',
  Overheat:   '#f59e0b',
  Slowdown:   '#3b82f6',
  Stagflation: '#f43f5e',
  Neutral:    '#64748b',
};

const CLASS_COLORS: Record<string, string> = {
  LEADING:   'text-emerald-600 dark:text-emerald-400',
  IMPROVING: 'text-blue-600 dark:text-blue-400',
  WEAKENING: 'text-amber-600 dark:text-amber-400',
  LAGGING:   'text-rose-600 dark:text-rose-400',
};
const CLASS_DOTS: Record<string, string> = {
  LEADING:   'bg-emerald-400',
  IMPROVING: 'bg-blue-400',
  WEAKENING: 'bg-amber-400',
  LAGGING:   'bg-rose-400',
};

export default function SectorDetailPage() {
  const params = useParams();
  const router = useRouter();
  const symbol = (params?.symbol as string || 'XLK').toUpperCase();

  const [sector, setSector] = useState<SectorDetail | null>(null);
  const [horizon, setHorizon] = useState<'tactical_50d' | 'strategic_260d'>('tactical_50d');
  const [loading, setLoading] = useState(true);

  const [perfHistory, setPerfHistory] = useState<any[]>([]);
  const [alphaMatrix, setAlphaMatrix] = useState<Record<string, any>>({});
  const [rankHistory, setRankHistory] = useState<any[]>([]);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`/api/sectors/${symbol}?horizon=${horizon}`).then(r => r.ok ? r.json() : null),
      fetch(`/api/sectors/${symbol}/performance?limit=12`).then(r => r.ok ? r.json() : []),
      fetch(`/api/sectors/analytics/regime-alpha-matrix`).then(r => r.ok ? r.json() : {}),
      fetch(`/api/sectors/scores/${symbol}/history?horizon=${horizon}&limit=252`).then(r => r.ok ? r.json() : []),
    ]).then(([sectorData, perf, matrix, rankHist]) => {
      if (sectorData && (sectorData.sector || sectorData.symbol)) {
        const sec = sectorData.sector || sectorData;
        const score = sectorData.score;
        setSector({
          id: sec.id || 1,
          symbol: sec.etf_ticker || sec.symbol || symbol,
          name: sec.name || symbol,
          description: sec.description || `Quant sector rotation profile for ${sec.name || symbol}.`,
          total_companies: sec.total_companies || sectorData.companies?.length || 0,
          latest_score: {
            overall_score: score?.composite_score ?? 50,
            rank: score?.rank || 1,
            classification: (score?.rrg_quadrant || 'LEADING').toUpperCase(),
            rs_ratio: score?.rs_ratio,
            rs_momentum: score?.rs_momentum,
            scores: score?.scores || {
              relative_strength: 50,
              momentum: 50,
              trend: 50,
              regime_fit: 75,
              risk: 80,
            }
          },
          companies: sectorData.companies || []
        });
      }
      if (Array.isArray(perf)) setPerfHistory(perf);
      if (matrix && typeof matrix === 'object') setAlphaMatrix(matrix);
      if (Array.isArray(rankHist)) setRankHistory(rankHist.slice().reverse());
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [symbol, horizon]);

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col bg-[var(--bg-main)] text-[var(--text-main)]">
        <Navbar />
        <main className="flex-1 flex items-center justify-center text-xs font-mono text-gray-400">Loading sector intelligence...</main>
      </div>
    );
  }

  if (!sector) {
    return (
      <div className="flex min-h-screen flex-col bg-[var(--bg-main)] text-[var(--text-main)]">
        <Navbar />
        <main className="flex-1 flex items-center justify-center text-xs font-mono text-gray-400">Sector not found.</main>
      </div>
    );
  }

  const sc = sector.latest_score.scores || { relative_strength: 50, momentum: 50, trend: 50, regime_fit: 50, risk: 50 };

  const latestPerf = perfHistory.length > 0 ? perfHistory[perfHistory.length - 1] : null;
  const perfBarData = latestPerf ? [
    { label: '1M', value: latestPerf.return_1m, raw: latestPerf.return_1m },
    { label: '3M', value: latestPerf.return_3m, raw: latestPerf.return_3m },
    { label: '6M', value: latestPerf.return_6m, raw: latestPerf.return_6m },
    { label: '12M', value: latestPerf.return_12m, raw: latestPerf.return_12m },
  ] : [];

  const QUADRANTS = ['Goldilocks', 'Overheat', 'Slowdown', 'Stagflation', 'Neutral'];
  const regimeAlphaRows = QUADRANTS.map(q => {
    const data = alphaMatrix[q]?.[symbol];
    return { quadrant: q, ...data };
  }).filter(r => r.avg_1m_return !== undefined || r.count !== undefined);

  return (
    <div className="flex min-h-screen flex-col bg-[var(--bg-main)] text-[var(--text-main)] transition-colors">
      <Navbar />

      <main className="flex-1 w-full px-4 sm:px-6 py-6 space-y-6">

        {/* ── Top Nav & Header Bar ── */}
        <div className="space-y-4 border-b border-[var(--border-color)] pb-6">
          <div className="flex items-center justify-between">
            <button onClick={() => router.back()}
              className="inline-flex items-center space-x-1.5 text-xs text-gray-500 hover:text-[var(--text-main)] transition-colors font-mono">
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Sector Rotation Engine</span>
            </button>

            {/* Horizon Selector */}
            <div className="flex items-center gap-2 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg p-1">
              <button
                onClick={() => setHorizon('tactical_50d')}
                className={`px-2.5 py-1 text-xs font-mono rounded transition-colors ${horizon === 'tactical_50d' ? 'bg-blue-600 text-white font-semibold' : 'text-gray-400 hover:text-[var(--text-main)]'}`}
              >
                Tactical (50D)
              </button>
              <button
                onClick={() => setHorizon('strategic_260d')}
                className={`px-2.5 py-1 text-xs font-mono rounded transition-colors ${horizon === 'strategic_260d' ? 'bg-blue-600 text-white font-semibold' : 'text-gray-400 hover:text-[var(--text-main)]'}`}
              >
                Strategic (260D)
              </button>
            </div>
          </div>

          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center space-x-3">
                <span className="text-3xl font-bold font-mono text-slate-900 dark:text-white">{sector.symbol}</span>
                <span className={`inline-flex items-center gap-1.5 text-xs font-semibold font-mono px-2.5 py-0.5 rounded-md border border-[var(--border-color)] bg-[var(--bg-card)] ${CLASS_COLORS[sector.latest_score.classification] || 'text-gray-400'}`}>
                  <span className={`h-2 w-2 rounded-full ${CLASS_DOTS[sector.latest_score.classification] || 'bg-gray-400'}`} />
                  RRG: {sector.latest_score.classification}
                </span>
              </div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight mt-1">{sector.name}</h1>
              <p className="text-xs text-gray-500 font-sans mt-1 max-w-2xl leading-relaxed">{sector.description}</p>
            </div>

            {/* Quick Cross-Link to ETF Profile & Composite Metric */}
            <div className="flex items-center space-x-6 shrink-0">
              <div className="text-right">
                <div className="text-[10px] font-mono text-gray-400 uppercase tracking-wider">Sector Score</div>
                <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
                  {sector.latest_score.overall_score.toFixed(1)} <span className="text-xs font-normal text-gray-400">/ 100</span>
                </div>
                <div className="text-[10px] font-mono text-gray-400">Rank #{sector.latest_score.rank} of 11</div>
              </div>

              <Link
                href={`/etfs/${sector.symbol}`}
                className="inline-flex items-center gap-1.5 text-xs font-mono px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors shadow-sm"
              >
                <span>ETF Fund & Risk Profile</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        </div>

        {/* ── Key Rotation & Relative Strength Cockpit ── */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-4 space-y-1">
            <p className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">RS-Ratio (vs SPY)</p>
            <p className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
              {sector.latest_score.rs_ratio ? sector.latest_score.rs_ratio.toFixed(2) : '—'}
            </p>
            <p className="text-[10px] text-gray-400">Relative Trend Baseline (100 = Market)</p>
          </div>

          <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-4 space-y-1">
            <p className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">RS-Momentum (vs SPY)</p>
            <p className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
              {sector.latest_score.rs_momentum ? sector.latest_score.rs_momentum.toFixed(2) : '—'}
            </p>
            <p className="text-[10px] text-gray-400">Relative Velocity (100 = Neutral)</p>
          </div>

          <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-4 space-y-1">
            <p className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">Horizon View</p>
            <p className="text-lg font-bold font-mono text-blue-500 uppercase">
              {horizon === 'tactical_50d' ? 'Tactical (50-Day)' : 'Strategic (260-Day)'}
            </p>
            <p className="text-[10px] text-gray-400">Lookback evaluation window</p>
          </div>

          <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-4 space-y-1">
            <p className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">Constituent Universe</p>
            <p className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
              {sector.total_companies || sector.companies.length} <span className="text-xs font-normal text-gray-400">Stocks</span>
            </p>
            <p className="text-[10px] text-gray-400">GICS sector constituent coverage</p>
          </div>
        </div>

        {/* ── Factor Scores Breakdown ── */}
        <section className="space-y-4 border-b border-[var(--border-color)] pb-6">
          <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">Sub-Factor Model Scoring</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 font-mono text-xs">
            {[
              { label: 'Rel Strength', val: sc.relative_strength },
              { label: 'Momentum', val: sc.momentum },
              { label: 'Trend', val: sc.trend },
              { label: 'Regime Fit', val: sc.regime_fit },
              { label: 'Risk', val: sc.risk },
              { label: 'Breadth Est', val: sc.breadth_estimate },
              { label: 'Fundamental', val: sc.fundamental },
              { label: 'Surprise Est', val: sc.surprise_estimate },
            ].filter(d => d.val !== undefined).map(d => {
              const v = d.val as number;
              const clr = v >= 65 ? 'text-emerald-500 dark:text-emerald-400' : v >= 45 ? 'text-slate-900 dark:text-white' : 'text-rose-500';
              const bg = v >= 65 ? 'bg-emerald-500' : v >= 45 ? 'bg-slate-400' : 'bg-rose-500';
              return (
                <div key={d.label} className="p-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] space-y-1.5">
                  <span className="text-gray-400 block text-[10px] uppercase tracking-wider leading-tight">{d.label}</span>
                  <div className={`text-lg font-bold ${clr}`}>{v.toFixed(0)}</div>
                  <div className="h-1 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${bg}`} style={{ width: `${Math.min(100, Math.max(0, v))}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* ── Rotation Score History Chart + Returns ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 border-b border-[var(--border-color)] pb-6">

          {/* Historical Composite Score Trajectory */}
          <div className="lg:col-span-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">Sector Score History (252-Day Trajectory)</h2>
              <span className="text-xs font-mono text-gray-400">Horizon: {horizon}</span>
            </div>
            {rankHistory.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={rankHistory} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748B', fontFamily: 'monospace' }}
                    tickFormatter={d => d.slice(5)} interval={Math.floor(rankHistory.length / 6)} stroke="#94A3B8" />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748B', fontFamily: 'monospace' }} stroke="#94A3B8" />
                  <Tooltip formatter={(v: any) => [v?.toFixed(1), 'Score']} contentStyle={{ backgroundColor: 'var(--bg-main)', borderColor: 'var(--border-color)', fontSize: '11px', fontFamily: 'monospace', borderRadius: '6px' }} />
                  <ReferenceLine y={50} stroke="var(--border-color)" strokeDasharray="4 4" />
                  <Line dataKey="composite_score" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : <p className="text-center text-xs font-mono text-gray-400 py-12">No score history data</p>}
          </div>

          {/* Performance Returns */}
          <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-4 space-y-4">
            <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">Sector ETF Returns</h2>
            <div className="grid grid-cols-2 gap-2">
              {perfBarData.map(p => (
                <div key={p.label} className="border border-[var(--border-color)] rounded-lg p-2.5 bg-[var(--bg-main)]">
                  <div className="text-[10px] font-mono text-gray-400 uppercase">{p.label} Return</div>
                  <div className={`text-base font-bold font-mono mt-0.5 ${p.raw >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                    {fmtReturn(p.raw)}
                  </div>
                </div>
              ))}
            </div>
            {perfBarData.length > 0 && (
              <div className="h-28">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={perfBarData} margin={{ top: 0, right: 4, bottom: 0, left: -25 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#64748B', fontFamily: 'monospace' }} />
                    <YAxis tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 9, fill: '#64748B', fontFamily: 'monospace' }} />
                    <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                      {perfBarData.map((entry, i) => (
                        <Cell key={i} fill={retColor(entry.raw)} fillOpacity={0.85} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>

        {/* ── Historical Performance by Macro Regime ── */}
        {regimeAlphaRows.length > 0 && (
          <section className="space-y-4 border-b border-[var(--border-color)] pb-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">
                Macro Regime Historical Alpha Fit
              </h2>
              <span className="text-[10px] font-mono text-gray-500">Historical performance across macro quadrants</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
              {regimeAlphaRows.map(row => {
                const color = REGIME_COLORS[row.quadrant] || '#64748b';
                const r1m = row.avg_1m_return;
                const r3m = row.avg_3m_return;
                return (
                  <div key={row.quadrant} className="border border-[var(--border-color)] rounded-lg p-3.5 bg-[var(--bg-card)] space-y-2.5">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: color }} />
                      <span className="font-mono font-bold text-[11px] text-slate-900 dark:text-white">{row.quadrant}</span>
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-gray-400 font-mono">Avg 1M Return</span>
                        <span className={`font-bold font-mono ${r1m >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                          {r1m !== undefined ? `${r1m >= 0 ? '+' : ''}${r1m.toFixed(2)}%` : '—'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-gray-400 font-mono">Avg 3M Return</span>
                        <span className={`font-bold font-mono ${r3m >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                          {r3m !== undefined ? `${r3m >= 0 ? '+' : ''}${r3m.toFixed(2)}%` : '—'}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* ── Constituent Equities Table ── */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">
                Sector Constituent Equities ({sector.companies.length} Companies)
              </h2>
              <p className="text-[11px] text-gray-500 mt-0.5 font-sans">
                Active equities classified under the {sector.name} GICS sector.
              </p>
            </div>
            <Link href="/stocks" className="text-xs font-mono text-blue-500 hover:underline">
              Explore All Stocks →
            </Link>
          </div>

          <div className="border border-[var(--border-color)] rounded-lg overflow-hidden bg-[var(--bg-card)]">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono border-collapse">
                <thead>
                  <tr className="border-b border-[var(--border-color)] text-gray-400 bg-[var(--bg-main)]">
                    <th className="py-3 px-4 font-normal">TICKER</th>
                    <th className="py-3 px-4 font-normal">COMPANY NAME</th>
                    <th className="py-3 px-4 font-normal">EXCHANGE</th>
                    <th className="py-3 px-4 font-normal">SUB-INDUSTRY</th>
                    <th className="py-3 px-4 font-normal text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-color)]">
                  {sector.companies && sector.companies.length > 0 ? (
                    sector.companies.map(comp => (
                      <tr key={comp.ticker}
                        onClick={() => router.push(`/stocks/${comp.ticker}`)}
                        className="hover:bg-[var(--bg-main)] transition-colors cursor-pointer">
                        <td className="py-3 px-4 font-bold text-slate-900 dark:text-white">{comp.ticker}</td>
                        <td className="py-3 px-4 text-slate-800 dark:text-slate-200 font-sans">{comp.company_name}</td>
                        <td className="py-3 px-4 text-gray-400">{comp.exchange}</td>
                        <td className="py-3 px-4 text-gray-400 font-sans">{comp.industry || '—'}</td>
                        <td className="py-3 px-4 text-right">
                          <span className="text-blue-500 hover:underline text-xs">Analyze →</span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-gray-400 font-sans">No constituent companies found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}
