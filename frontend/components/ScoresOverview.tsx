'use client';

import React, { useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

interface ScoresOverviewProps {
  currentRegime: any;
  history: any[];
  loading?: boolean;
}

// Fix 2 helper: compute trend arrow and delta label
function getTrend(current: number, prev: number | undefined): { arrow: string; delta: string; color: string } {
  if (prev === undefined || prev === null) return { arrow: '—', delta: '', color: 'text-gray-400' };
  const diff = current - prev;
  if (Math.abs(diff) < 1) return { arrow: '→', delta: `${diff >= 0 ? '+' : ''}${diff.toFixed(1)}`, color: 'text-gray-400' };
  if (diff > 0) return { arrow: '↑', delta: `+${diff.toFixed(1)}`, color: 'text-gray-400' };
  return { arrow: '↓', delta: `${diff.toFixed(1)}`, color: 'text-gray-400' };
}

// Fix 2 helper: color score band (≥65 good, ≥50 neutral, ≥35 caution, <35 risk)
function getScoreColor(score: number): string {
  if (score >= 65) return 'text-emerald-600 dark:text-emerald-400';
  if (score >= 50) return 'text-slate-900 dark:text-white';
  if (score >= 35) return 'text-amber-600 dark:text-amber-400';
  return 'text-rose-600 dark:text-rose-400';
}

function getScoreBg(score: number): string {
  if (score >= 65) return 'bg-emerald-500';
  if (score >= 50) return 'bg-slate-400';
  if (score >= 35) return 'bg-amber-500';
  return 'bg-rose-500';
}

function getQuadrantColor(quadrant: string) {
  switch (quadrant) {
    case 'Goldilocks': return { dot: 'bg-emerald-400', text: 'text-emerald-600 dark:text-emerald-400', border: 'border-emerald-500/30', bg: 'bg-emerald-500/5' };
    case 'Overheat': return { dot: 'bg-amber-400', text: 'text-amber-600 dark:text-amber-400', border: 'border-amber-500/30', bg: 'bg-amber-500/5' };
    case 'Slowdown': return { dot: 'bg-blue-400', text: 'text-blue-600 dark:text-blue-400', border: 'border-blue-500/30', bg: 'bg-blue-500/5' };
    case 'Stagflation': return { dot: 'bg-rose-400', text: 'text-rose-600 dark:text-rose-400', border: 'border-rose-500/30', bg: 'bg-rose-500/5' };
    default: return { dot: 'bg-gray-400', text: 'text-gray-500', border: 'border-gray-400/30', bg: 'bg-gray-500/5' };
  }
}

export const ScoresOverview: React.FC<ScoresOverviewProps> = ({ currentRegime, history, loading }) => {
  const [chartMode, setChartMode] = useState<'overall' | 'dimensions'>('overall');

  const dims = currentRegime?.dimensions || {};
  const prevDims = currentRegime?.prev_dimensions || {};

  const getScore = (key: string) => {
    if (dims[key] !== undefined && dims[key] !== null) return Math.round(dims[key]);
    return 0;
  };

  const dimensionsList = [
    { key: 'growth', name: 'Growth', score: getScore('growth'), desc: 'GDP, Industrial Production, Retail Sales, Unemployment' },
    { key: 'inflation', name: 'Inflation', score: getScore('inflation'), desc: 'CPI, Core CPI, PCE Price Index' },
    { key: 'rates', name: 'Interest Rates', score: getScore('rates'), desc: 'Fed Funds, Yield Curve, Real Yields' },
    { key: 'liquidity', name: 'Liquidity', score: getScore('liquidity'), desc: 'M2 Money Supply, Fed Total Assets' },
    { key: 'credit', name: 'Credit Spreads', score: getScore('credit'), desc: 'High Yield OAS Spread' },
    { key: 'risk', name: 'Market Risk', score: getScore('risk'), desc: 'CBOE VIX Volatility Index' },
  ];

  const positiveDrivers = currentRegime?.positive || currentRegime?.why?.positive || [];
  const negativeDrivers = currentRegime?.negative || currentRegime?.why?.negative || [];

  // Fix 5: use ETF-enriched tilt lists if available
  const favoredAssets: any[] = currentRegime?.favored_assets_with_etf || (currentRegime?.favored_assets || []).map((a: string) => ({ label: a, etf: null, name: a }));
  const avoidAssets: any[] = currentRegime?.avoid_assets_with_etf || (currentRegime?.avoid_assets || []).map((a: string) => ({ label: a, etf: null, name: a }));

  const formattedData = (history || []).map((item) => ({
    date: item.feature_date || item.date,
    Overall: Math.round(item.overall_score || 0),
    Growth: Math.round(item.growth_score || item.dimensions?.growth || 0),
    Inflation: Math.round(item.inflation_score || item.dimensions?.inflation || 0),
    Rates: Math.round(item.rates_score || item.dimensions?.rates || 0),
    Liquidity: Math.round(item.liquidity_score || item.dimensions?.liquidity || 0),
    Credit: Math.round(item.credit_score || item.dimensions?.credit || 0),
    Risk: Math.round(item.risk_score || item.dimensions?.risk || 0),
  }));

  const qColors = getQuadrantColor(currentRegime?.quadrant);

  // Fix 4: Duration progress bar value
  const duration = currentRegime?.regime_duration_days ?? 1;
  const avgDuration = currentRegime?.avg_regime_duration_days ?? 30;
  const durationPct = Math.min(100, Math.round((duration / Math.max(avgDuration, 1)) * 100));

  if (loading || !currentRegime) {
    return (
      <div className="flex items-center justify-center h-48 text-xs font-mono text-gray-500">
        Loading regime data...
      </div>
    );
  }

  return (
    <div className="space-y-8 pt-2 w-full">

      {/* 1. Hero / Current Macro Regime Section */}
      <div className={`rounded-xl border ${qColors.border} bg-[var(--bg-main)] p-5 space-y-4`}>
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className={`h-2.5 w-2.5 rounded-full animate-pulse ${qColors.dot}`} />
              <span className="text-[10px] font-mono text-gray-400 uppercase tracking-wider">Current Macro Regime</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white tracking-tight leading-tight">
              {currentRegime.regime}
            </h2>
            <div className={`text-xs font-mono mt-1 ${qColors.text}`}>
              {currentRegime.quadrant} Quadrant · {currentRegime.severity}
            </div>
          </div>

          {/* Regime Duration Counter */}
          <div className="shrink-0 text-left space-y-1">
            <div className="text-[10px] font-mono text-gray-400 uppercase tracking-wider">Regime Duration</div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white font-mono">
              {duration}<span className="text-sm font-normal text-gray-400"> days</span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <div className="h-1 w-32 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${durationPct >= 100 ? 'bg-amber-400' : qColors.dot.replace('bg-', 'bg-')}`}
                  style={{ width: `${durationPct}%` }}
                />
              </div>
              <span className="text-[10px] font-mono text-gray-400">
                avg {avgDuration}d
              </span>
            </div>
            {currentRegime.regime_started && (
              <div className="text-[10px] text-gray-400 font-mono">
                Since {currentRegime.regime_started}
              </div>
            )}
          </div>
        </div>

        {/* Compact key metrics row */}
        <div className="flex flex-wrap gap-6 text-xs font-mono pt-1 border-t border-[var(--border-color)]/40">
          <div>
            <div className="text-gray-400 text-[10px] uppercase tracking-wider">Composite Score</div>
            <div className="text-lg font-bold text-slate-900 dark:text-white">
              {currentRegime.overall_score}
              <span className="text-xs font-normal text-gray-400"> / 100</span>
            </div>
          </div>
          <div>
            <div className="text-gray-400 text-[10px] uppercase tracking-wider">Signal Confidence</div>
            <div className="text-lg font-bold text-slate-900 dark:text-white">
              {currentRegime.confidence}%
            </div>
          </div>
          <div>
            <div className="text-gray-400 text-[10px] uppercase tracking-wider">FCA</div>
            <div className="text-lg font-bold text-slate-900 dark:text-white">
              {currentRegime.fca?.score !== undefined
                ? (currentRegime.fca.score >= 0 ? `+${currentRegime.fca.score}` : currentRegime.fca.score)
                : 'N/A'}
              <span className="text-xs font-normal text-gray-400 ml-1">({currentRegime.fca?.status || 'Neutral'})</span>
            </div>
          </div>
          <div>
            <div className="text-gray-400 text-[10px] uppercase tracking-wider">Policy Stance</div>
            <div className={`text-lg font-bold ${currentRegime.policy_stance === 'Restrictive' ? 'text-rose-500' : 'text-emerald-500'}`}>
              {currentRegime.policy_stance || 'N/A'}
            </div>
          </div>
          <div>
            <div className="text-gray-400 text-[10px] uppercase tracking-wider">3M Δ Growth / Inflation</div>
            <div className="text-lg font-bold text-slate-900 dark:text-white font-mono">
              <span className={currentRegime.delta_growth > 0 ? 'text-emerald-500' : currentRegime.delta_growth < 0 ? 'text-rose-500' : 'text-gray-400'}>
                {currentRegime.delta_growth > 0 ? '+' : ''}{currentRegime.delta_growth ?? '0'}
              </span>
              <span className="text-gray-400 mx-1">/</span>
              <span className={currentRegime.delta_inflation > 0 ? 'text-amber-500' : currentRegime.delta_inflation < 0 ? 'text-emerald-500' : 'text-gray-400'}>
                {currentRegime.delta_inflation > 0 ? '+' : ''}{currentRegime.delta_inflation ?? '0'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Dimension Scores Breakdown */}
      <div className="space-y-4 border-b border-[var(--border-color)] pb-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider">
            Dimension Scores Breakdown
          </h3>
          <span className="text-[10px] font-mono text-gray-400">
            {prevDims && Object.keys(prevDims).length > 0 ? 'Arrows show 30-day change' : 'No prior data for trend'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {dimensionsList.map((d) => {
            const trend = getTrend(d.score, prevDims?.[d.key]);
            const barPct = Math.min(100, d.score);
            return (
              <div key={d.name} className="border border-[var(--border-color)] rounded-lg p-3.5 bg-[var(--bg-main)] space-y-2.5">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-slate-900 dark:text-white">{d.name}</div>
                    <div className="text-[10px] text-gray-500 font-light mt-0.5 leading-tight">{d.desc}</div>
                  </div>
                  <div className="flex items-baseline gap-1.5 text-right">
                    <span className={`text-xl font-mono font-bold ${getScoreColor(d.score)}`}>
                      {d.score}
                    </span>
                    {prevDims?.[d.key] !== undefined && (
                      <span className={`text-xs font-mono font-semibold ${trend.color}`} title={`30d change: ${trend.delta}`}>
                        {trend.arrow}
                      </span>
                    )}
                  </div>
                </div>
                {/* Score bar */}
                <div className="h-1 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${getScoreBg(d.score)}`}
                    style={{ width: `${barPct}%` }}
                  />
                </div>
                {prevDims?.[d.key] !== undefined && (
                  <div className={`text-[10px] font-mono ${trend.color}`}>
                    {trend.delta !== '' ? `30d: ${trend.delta}` : '30d: flat'}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Regime Asset Tilt Recommendations */}
      {(favoredAssets.length > 0 || avoidAssets.length > 0) && (
        <div className="space-y-3.5 border-b border-[var(--border-color)] pb-6">
          <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider">
            Regime Asset Tilt Recommendations
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            {/* Favored */}
            <div className="border border-[var(--border-color)] rounded-lg p-4 bg-[var(--bg-main)] space-y-2.5">
              <div className="font-semibold text-slate-900 dark:text-white flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                Overweight / Favor
              </div>
              <div className="flex flex-wrap gap-2">
                {favoredAssets.map((asset: any, i: number) => (
                  <div key={i} className="flex flex-col items-start rounded-md bg-[var(--bg-main)] border border-[var(--border-color)] px-2.5 py-1.5">
                    <span className="font-mono font-bold text-[11px] text-slate-900 dark:text-white">
                      {asset.etf || asset.label}
                    </span>
                    <span className="text-[10px] text-gray-500 font-sans leading-tight">
                      {asset.etf ? asset.label : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Avoid */}
            <div className="border border-[var(--border-color)] rounded-lg p-4 bg-[var(--bg-main)] space-y-2.5">
              <div className="font-semibold text-slate-900 dark:text-white flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider">
                <span className="h-2 w-2 rounded-full bg-rose-500" />
                Underweight / Avoid
              </div>
              <div className="flex flex-wrap gap-2">
                {avoidAssets.map((asset: any, i: number) => (
                  <div key={i} className="flex flex-col items-start rounded-md bg-[var(--bg-main)] border border-[var(--border-color)] px-2.5 py-1.5">
                    <span className="font-mono font-bold text-[11px] text-slate-900 dark:text-white">
                      {asset.etf || asset.label}
                    </span>
                    <span className="text-[10px] text-gray-500 font-sans leading-tight">
                      {asset.etf ? asset.label : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Regime Drivers & Headwinds */}
      <div className="space-y-4 border-b border-[var(--border-color)] pb-6">
        <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider">
          Regime Drivers &amp; Headwinds
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          <div className="space-y-2">
            <div className="font-semibold text-slate-900 dark:text-white text-[11px] uppercase tracking-wider font-mono">Positive Support Factors</div>
            {positiveDrivers.length === 0 ? (
              <div className="text-gray-400 font-mono text-xs">No drivers recorded</div>
            ) : (
              <ul className="space-y-1.5 text-gray-600 dark:text-gray-400">
                {positiveDrivers.map((item: string, idx: number) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-gray-400 font-bold mt-0.5">+</span>
                    <span className="font-sans">{item}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="space-y-2">
            <div className="font-semibold text-slate-900 dark:text-white text-[11px] uppercase tracking-wider font-mono">Headwinds &amp; Risks</div>
            {negativeDrivers.length === 0 ? (
              <div className="text-gray-400 font-mono text-xs">No headwinds recorded</div>
            ) : (
              <ul className="space-y-1.5 text-gray-600 dark:text-gray-400">
                {negativeDrivers.map((item: string, idx: number) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-gray-400 font-bold mt-0.5">−</span>
                    <span className="font-sans">{item}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* 5. Sub-Dimension Divergence Signals */}
      {currentRegime?.divergences && currentRegime.divergences.length > 0 && (
        <div className="space-y-3 border-b border-[var(--border-color)] pb-6">
          <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider">
            Sub-Dimension Divergence Signals
          </h3>
          <div className="space-y-2">
            {currentRegime.divergences.map((divText: string, idx: number) => (
              <div
                key={idx}
                className="pl-4 pr-3.5 py-2.5 rounded-r-lg border-l-2 border-blue-600 bg-slate-100/60 dark:bg-slate-800/35 text-slate-800 dark:text-slate-200 font-sans text-xs leading-relaxed transition-all duration-200 hover:bg-slate-200/50 dark:hover:bg-slate-800/60 hover:translate-x-0.5"
              >
                <div>
                  <span>{divText}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6. Historical Score Trajectory */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider">
            Historical Score Trajectory
          </h3>
          <div className="flex space-x-3 text-xs font-mono">
            <button
              onClick={() => setChartMode('overall')}
              className={`transition-colors ${chartMode === 'overall' ? 'font-bold text-[var(--text-main)] underline underline-offset-4' : 'text-gray-500 hover:text-[var(--text-main)]'}`}
            >
              Overall
            </button>
            <button
              onClick={() => setChartMode('dimensions')}
              className={`transition-colors ${chartMode === 'dimensions' ? 'font-bold text-[var(--text-main)] underline underline-offset-4' : 'text-gray-500 hover:text-[var(--text-main)]'}`}
            >
              Dimensions
            </button>
          </div>
        </div>

        <div className="h-56 w-full">
          {formattedData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs font-mono text-gray-500 border border-[var(--border-color)] rounded-lg">
              No historical scores recorded in database.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              {chartMode === 'overall' ? (
                <AreaChart data={formattedData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                  <XAxis dataKey="date" stroke="#94A3B8" tick={{ fontSize: 10, fill: '#64748B' }} />
                  <YAxis domain={[0, 100]} stroke="#94A3B8" tick={{ fontSize: 10, fill: '#64748B' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'var(--bg-main)', borderColor: 'var(--border-color)', borderRadius: '6px', fontSize: '11px', fontFamily: 'monospace' }}
                  />
                  <Area type="monotone" dataKey="Overall" stroke="#2563EB" strokeWidth={2} fillOpacity={0.08} fill="#2563EB" />
                </AreaChart>
              ) : (
                <LineChart data={formattedData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                  <XAxis dataKey="date" stroke="#94A3B8" tick={{ fontSize: 10, fill: '#64748B' }} />
                  <YAxis domain={[0, 100]} stroke="#94A3B8" tick={{ fontSize: 10, fill: '#64748B' }} />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--bg-main)', borderColor: 'var(--border-color)', borderRadius: '6px', fontSize: '11px', fontFamily: 'monospace' }} />
                  <Line type="monotone" dataKey="Growth" stroke="#3B82F6" strokeWidth={1.5} dot={false} />
                  <Line type="monotone" dataKey="Inflation" stroke="#F59E0B" strokeWidth={1.5} dot={false} />
                  <Line type="monotone" dataKey="Rates" stroke="#8B5CF6" strokeWidth={1.5} dot={false} />
                  <Line type="monotone" dataKey="Liquidity" stroke="#10B981" strokeWidth={1.5} dot={false} />
                  <Line type="monotone" dataKey="Credit" stroke="#06B6D4" strokeWidth={1.5} dot={false} />
                  <Line type="monotone" dataKey="Risk" stroke="#F43F5E" strokeWidth={1.5} dot={false} />
                </LineChart>
              )}
            </ResponsiveContainer>
          )}
        </div>
      </div>

    </div>
  );
};
