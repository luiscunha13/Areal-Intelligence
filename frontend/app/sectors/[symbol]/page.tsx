'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { Navbar } from '@/components/Navbar';
import { ArrowLeft, ChevronRight } from 'lucide-react';
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
    scores?: {
      momentum: number;
      relative_strength: number;
      trend: number;
      regime_fit: number;
      risk: number;
      surprise?: number;
      breadth?: number;
      fundamental?: number;
    };
    pe_ratio_ttm?: number;
    eps_growth_yoy?: number;
    revenue_growth_yoy?: number;
    eps_surprise_pct?: number;
    rs_ratio?: number;
    rs_momentum?: number;
  };
  companies: Array<{
    id: number;
    ticker: string;
    company_name: string;
    exchange: string;
    market_cap?: number;
  }>;
}

// Fix 4: color by return value
function retColor(v: number | null | undefined): string {
  if (v === null || v === undefined) return '#64748b';
  return v >= 0 ? '#10b981' : '#f43f5e';
}

function fmtReturn(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—';
  return `${v >= 0 ? '+' : ''}${(v * 100).toFixed(2)}%`;
}

// Fix 5: regime quadrant colors
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
  const symbol = (params?.symbol as string || 'XLK').toUpperCase();

  const [sector, setSector] = useState<SectorDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // Fix 4: performance history
  const [perfHistory, setPerfHistory] = useState<any[]>([]);
  // Fix 5: regime alpha matrix
  const [alphaMatrix, setAlphaMatrix] = useState<Record<string, any>>({});
  // Fix 2: rank history chart
  const [rankHistory, setRankHistory] = useState<any[]>([]);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`http://127.0.0.1:8000/api/sectors/${symbol}`).then(r => r.ok ? r.json() : null),
      fetch(`http://127.0.0.1:8000/api/sectors/${symbol}/performance?limit=12`).then(r => r.ok ? r.json() : []),
      fetch(`http://127.0.0.1:8000/api/sectors/analytics/regime-alpha-matrix`).then(r => r.ok ? r.json() : {}),
      fetch(`http://127.0.0.1:8000/api/sectors/${symbol}/rank-history?limit=20`).then(r => r.ok ? r.json() : []),
    ]).then(([sectorData, perf, matrix, rankHist]) => {
      if (sectorData?.symbol) setSector(sectorData);
      if (Array.isArray(perf)) setPerfHistory(perf);
      if (matrix && typeof matrix === 'object') setAlphaMatrix(matrix);
      if (Array.isArray(rankHist)) setRankHistory(rankHist);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [symbol]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-main)]">
        <Navbar />
        <main className="w-full px-6 py-12 text-center text-gray-400 font-mono text-xs">Loading sector data...</main>
      </div>
    );
  }

  if (!sector) {
    return (
      <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-main)]">
        <Navbar />
        <main className="w-full px-6 py-12 text-center text-gray-400 font-mono">Sector not found.</main>
      </div>
    );
  }

  const sc = sector.latest_score.scores || { momentum: 50, relative_strength: 50, trend: 50, regime_fit: 50, risk: 50 };

  // Fix 4: latest perf record
  const latestPerf = perfHistory.length > 0 ? perfHistory[perfHistory.length - 1] : null;
  const perfBarData = latestPerf ? [
    { label: '1M', value: latestPerf.return_1m, raw: latestPerf.return_1m },
    { label: '3M', value: latestPerf.return_3m, raw: latestPerf.return_3m },
    { label: '6M', value: latestPerf.return_6m, raw: latestPerf.return_6m },
    { label: '12M', value: latestPerf.return_12m, raw: latestPerf.return_12m },
  ] : [];

  // Fix 5: this sector's performance per regime
  const QUADRANTS = ['Goldilocks', 'Overheat', 'Slowdown', 'Stagflation', 'Neutral'];
  const regimeAlphaRows = QUADRANTS.map(q => {
    const data = alphaMatrix[q]?.[symbol];
    return { quadrant: q, ...data };
  }).filter(r => r.avg_1m_return !== undefined || r.count !== undefined);

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg-main)] text-[var(--text-main)] transition-colors">
      <Navbar />

      <main className="flex-1 w-full px-4 sm:px-6 py-4 space-y-6">

        {/* Back Link & Header */}
        <div className="space-y-4 border-b border-[var(--border-color)] pb-6">
          <Link href="/sectors" className="inline-flex items-center space-x-1.5 text-xs text-gray-500 hover:text-[var(--text-main)] transition-colors font-mono">
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Sector Rotation Engine</span>
          </Link>

          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <div className="flex items-center space-x-3">
                <span className="text-3xl font-bold font-mono text-slate-900 dark:text-white">{sector.symbol}</span>
                <span className={`inline-flex items-center gap-1.5 text-[10px] font-semibold font-mono ${CLASS_COLORS[sector.latest_score.classification] || 'text-gray-400'}`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${CLASS_DOTS[sector.latest_score.classification] || 'bg-gray-400'}`} />
                  {sector.latest_score.classification}
                </span>
              </div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight mt-1">{sector.name}</h1>
              <p className="text-xs text-gray-500 font-sans mt-1 max-w-2xl leading-relaxed">{sector.description}</p>
            </div>

            <div className="flex items-center space-x-8 text-xs font-mono shrink-0">
              <div>
                <div className="text-gray-400 text-[10px] uppercase tracking-wider">Composite Score</div>
                <div className="text-xl font-bold text-slate-900 dark:text-white">
                  {sector.latest_score.overall_score.toFixed(1)} <span className="text-xs font-normal text-gray-400">/ 100</span>
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-[10px] uppercase tracking-wider">GICS Rank</div>
                <div className="text-xl font-bold text-slate-900 dark:text-white">{sector.latest_score.rank}</div>
              </div>
              {sector.latest_score.rs_ratio && (
                <div>
                  <div className="text-gray-400 text-[10px] uppercase tracking-wider">RS Ratio</div>
                  <div className="text-xl font-bold text-slate-900 dark:text-white">{sector.latest_score.rs_ratio.toFixed(2)}</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Factor Score Gauges */}
        <section className="space-y-4 border-b border-[var(--border-color)] pb-6">
          <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">Factor Scores Breakdown</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 font-mono text-xs">
            {[
              { label: 'Rel Strength', val: sc.relative_strength },
              { label: 'Momentum', val: sc.momentum },
              { label: 'Trend', val: sc.trend },
              { label: 'Regime Fit', val: sc.regime_fit },
              { label: 'Risk', val: sc.risk },
              { label: 'Breadth', val: sc.breadth },
              { label: 'Fundamental', val: sc.fundamental },
              { label: 'Surprise', val: sc.surprise },
            ].filter(d => d.val !== undefined).map(d => {
              const v = d.val as number;
              const clr = v >= 65 ? 'text-emerald-500 dark:text-emerald-400' : v >= 45 ? 'text-slate-900 dark:text-white' : 'text-rose-500';
              const bg = v >= 65 ? 'bg-emerald-500' : v >= 45 ? 'bg-slate-400' : 'bg-rose-500';
              return (
                <div key={d.label} className="p-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1.5">
                  <span className="text-gray-400 block text-[10px] uppercase tracking-wider leading-tight">{d.label}</span>
                  <div className={`text-lg font-bold ${clr}`}>{v}</div>
                  <div className="h-0.5 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${bg}`} style={{ width: `${Math.min(100, v)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Fix 4: Performance Returns — Bar chart + return pills */}
        {(latestPerf || perfHistory.length > 0) && (
          <section className="space-y-4 border-b border-[var(--border-color)] pb-6">
            <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">ETF Performance Returns</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Return pills */}
              <div className="flex flex-wrap gap-3 content-start">
                {perfBarData.map(p => (
                  <div key={p.label} className="border border-[var(--border-color)] rounded-lg px-4 py-3 bg-[var(--bg-main)] min-w-[90px]">
                    <div className="text-[10px] font-mono text-gray-400 uppercase tracking-wider">{p.label} Return</div>
                    <div className={`text-xl font-bold font-mono mt-1 ${p.raw >= 0 ? 'text-emerald-500 dark:text-emerald-400' : 'text-rose-500'}`}>
                      {fmtReturn(p.raw)}
                    </div>
                  </div>
                ))}
              </div>
              {/* Bar chart of period returns */}
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={perfBarData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#64748B', fontFamily: 'monospace' }} stroke="#94A3B8" />
                    <YAxis tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 10, fill: '#64748B', fontFamily: 'monospace' }} stroke="#94A3B8" />
                    <Tooltip formatter={(v: any) => [`${(v * 100).toFixed(2)}%`]} contentStyle={{ backgroundColor: 'var(--bg-main)', borderColor: 'var(--border-color)', fontSize: '11px', fontFamily: 'monospace', borderRadius: '6px' }} />
                    <ReferenceLine y={0} stroke="#64748B" strokeWidth={1} />
                    <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                      {perfBarData.map((entry, i) => (
                        <Cell key={i} fill={retColor(entry.raw)} fillOpacity={0.85} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>
        )}

        {/* Fix 5: Regime–Sector Alpha Matrix */}
        {regimeAlphaRows.length > 0 && (
          <section className="space-y-4 border-b border-[var(--border-color)] pb-6">
            <div className="flex items-center gap-2">
              <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">
                Historical Performance by Macro Regime
              </h2>
              <span className="text-[10px] font-mono text-gray-500">(avg across {regimeAlphaRows.reduce((a, r) => a + (r.count || 0), 0)} regime periods)</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
              {regimeAlphaRows.map(row => {
                const color = REGIME_COLORS[row.quadrant] || '#64748b';
                const r1m = row.avg_1m_return;
                const r3m = row.avg_3m_return;
                return (
                  <div key={row.quadrant} className="border border-[var(--border-color)] rounded-lg p-3.5 bg-[var(--bg-main)] space-y-2.5">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: color }} />
                      <span className="font-mono font-bold text-[11px] text-slate-900 dark:text-white">{row.quadrant}</span>
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-gray-400 font-mono">Avg 1M</span>
                        <span className={`font-bold font-mono ${r1m >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                          {r1m !== undefined ? `${r1m >= 0 ? '+' : ''}${r1m.toFixed(2)}%` : '—'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-gray-400 font-mono">Avg 3M</span>
                        <span className={`font-bold font-mono ${r3m >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                          {r3m !== undefined ? `${r3m >= 0 ? '+' : ''}${r3m.toFixed(2)}%` : '—'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-gray-400 font-mono">Periods</span>
                        <span className="font-mono text-gray-500">{row.count ?? '—'}</span>
                      </div>
                    </div>
                    {/* mini bar showing 1M return */}
                    {r1m !== undefined && (
                      <div className="h-0.5 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${Math.min(100, Math.abs(r1m) * 5)}%`,
                            backgroundColor: color,
                            marginLeft: r1m < 0 ? 'auto' : undefined,
                          }}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Sector Driver Analysis */}
        {sector.why && sector.why.length > 0 && (
          <section className="space-y-4 border-b border-[var(--border-color)] pb-6">
            <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">Sector Driver Analysis & Rationale</h2>
            <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-main)] p-4 space-y-2.5">
              {sector.why.map((reason, idx) => (
                <div key={idx} className="flex items-start space-x-2 text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
                  <span className="text-gray-400 font-mono mt-0.5">—</span>
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Constituent Equities */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">
              Constituent Equities (Top {sector.companies?.length || 0} of {sector.total_companies || sector.companies?.length || 0} by Market Cap)
            </h2>
            <Link href="/stocks" className="text-xs font-mono text-gray-400 hover:text-[var(--text-main)] transition-colors">
              Explore All Stocks →
            </Link>
          </div>

          <div className="border border-[var(--border-color)] rounded-lg overflow-hidden bg-[var(--bg-main)]">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono border-collapse">
                <thead>
                  <tr className="border-b border-[var(--border-color)] text-gray-400">
                    <th className="py-3 px-4 font-mono font-normal">TICKER</th>
                    <th className="py-3 px-4 font-mono font-normal">COMPANY NAME</th>
                    <th className="py-3 px-4 font-mono font-normal">EXCHANGE</th>
                    <th className="py-3 px-4 font-mono font-normal text-right">EST. MARKET CAP</th>
                    <th className="py-3 px-4 font-mono font-normal text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-color)]/60">
                  {sector.companies && sector.companies.length > 0 ? (
                    sector.companies.map(comp => (
                      <tr key={comp.ticker} className="hover:bg-slate-500/5 transition-colors">
                        <td className="py-3 px-4 font-bold text-slate-900 dark:text-white">
                          <Link href={`/stocks/${comp.ticker}`} className="hover:underline">{comp.ticker}</Link>
                        </td>
                        <td className="py-3 px-4 font-sans text-slate-800 dark:text-slate-200">
                          <Link href={`/stocks/${comp.ticker}`} className="hover:underline">{comp.company_name}</Link>
                        </td>
                        <td className="py-3 px-4 text-gray-400">{comp.exchange}</td>
                        <td className="py-3 px-4 text-right text-gray-500">
                          {comp.market_cap ? `$${(comp.market_cap / 1e9).toFixed(1)}B` : '—'}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Link href={`/stocks/${comp.ticker}`} className="inline-flex items-center space-x-1 text-gray-400 hover:text-[var(--text-main)] text-xs transition-colors">
                            <span>View</span>
                            <ChevronRight className="h-3 w-3" />
                          </Link>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-gray-400 font-sans">No constituents available.</td>
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
