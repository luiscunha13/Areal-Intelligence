'use client';

import React, { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import { Navbar } from '../../components/Navbar';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Label,
} from 'recharts';

interface SectorItem {
  symbol: string;
  name: string;
  gics_code?: string;
  rank: number;
  rank_change: number;
  overall_score: number;
  rs_ratio?: number;
  rs_momentum?: number;
  scores?: {
    momentum: number;
    relative_strength: number;
    trend: number;
    regime_fit: number;
    risk: number;
    surprise?: number;
  };
  classification: 'LEADING' | 'IMPROVING' | 'WEAKENING' | 'LAGGING' | string;
  why: string[];
}

// Fix 3: Color scoring for score cells
function scoreColor(v: number | undefined): string {
  if (v === undefined) return 'text-gray-400';
  if (v >= 70) return 'text-emerald-600 dark:text-emerald-400';
  if (v >= 55) return 'text-slate-700 dark:text-slate-200';
  if (v >= 40) return 'text-amber-600 dark:text-amber-400';
  return 'text-rose-600 dark:text-rose-400';
}

// Classification colors
const QUAD_COLORS: Record<string, { dot: string; fill: string; text: string }> = {
  LEADING:   { dot: 'bg-emerald-400', fill: '#10b981', text: 'text-emerald-600 dark:text-emerald-400' },
  IMPROVING: { dot: 'bg-blue-400',    fill: '#3b82f6', text: 'text-blue-600 dark:text-blue-400' },
  WEAKENING: { dot: 'bg-amber-400',   fill: '#f59e0b', text: 'text-amber-600 dark:text-amber-400' },
  LAGGING:   { dot: 'bg-rose-400',    fill: '#f43f5e', text: 'text-rose-600 dark:text-rose-400' },
};

// Fix 1: Custom RRG scatter dot with dynamic 2D repulsion pointer lines & labels
const RRGDot = (props: any) => {
  const { cx, cy, payload } = props;
  if (cx === undefined || cy === undefined) return null;
  const c = QUAD_COLORS[payload.classification] || QUAD_COLORS.LAGGING;
  const off = payload.labelOffset || { dx: 14, dy: -12, textAnchor: 'start' };

  const endX = cx + off.dx;
  const endY = cy + off.dy;

  return (
    <g className="cursor-pointer group">
      {/* Soft halo */}
      <circle cx={cx} cy={cy} r={6} fill={c.fill} fillOpacity={0.25} />
      {/* Core colored dot */}
      <circle cx={cx} cy={cy} r={3.5} fill={c.fill} stroke="var(--bg-main)" strokeWidth={1} />

      {/* Pointer line directed into empty space */}
      <line
        x1={cx}
        y1={cy}
        x2={endX}
        y2={endY}
        stroke="currentColor"
        strokeWidth={1}
        strokeOpacity={0.6}
        className="text-slate-600 dark:text-slate-400"
      />

      {/* Ticker label positioned at end of pointer line */}
      <text
        x={endX + (off.dx > 3 ? 3 : off.dx < -3 ? -3 : 0)}
        y={endY}
        textAnchor={off.textAnchor as any}
        dominantBaseline="central"
        fontSize={10}
        fontWeight="700"
        fill="currentColor"
        fontFamily="monospace"
        className="select-none text-slate-900 dark:text-white"
      >
        {payload.symbol}
      </text>
    </g>
  );
};

// Fix 1: Custom RRG tooltip
const RRGTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const c = QUAD_COLORS[d.classification] || QUAD_COLORS.LAGGING;
  return (
    <div className="bg-[var(--bg-main)] border border-[var(--border-color)] rounded-lg p-3 text-xs font-mono shadow-xl z-50 space-y-1.5 min-w-[180px]">
      <div className="flex items-center gap-2 border-b border-[var(--border-color)] pb-1.5">
        <span className={`h-2 w-2 rounded-full ${c.dot}`} />
        <span className="font-bold text-slate-900 dark:text-white">{d.symbol}</span>
        <span className="text-gray-400 font-sans text-[10px]">{d.name}</span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]">
        <span className="text-gray-400">RS Ratio</span><span className="font-bold text-slate-900 dark:text-white">{d.rs_ratio?.toFixed(2)}</span>
        <span className="text-gray-400">RS Momentum</span><span className="font-bold text-slate-900 dark:text-white">{d.rs_momentum?.toFixed(2)}</span>
        <span className="text-gray-400">Score</span><span className="font-bold text-slate-900 dark:text-white">{d.overall_score}</span>
        <span className="text-gray-400">Rank</span><span className="font-bold text-slate-900 dark:text-white">{d.rank}</span>
      </div>
      <div className={`text-[10px] font-semibold uppercase tracking-wider ${c.text}`}>{d.classification}</div>
    </div>
  );
};

// Fix 2: Mini sparkline for rank history (inline SVG)
function RankSparkline({ ranks, total }: { ranks: number[]; total: number }) {
  if (!ranks || ranks.length < 2) return <span className="text-gray-400 text-[10px] font-mono">—</span>;
  const w = 52, h = 16, pad = 2;
  const min = 1, max = Math.max(total, ...ranks);
  const pts = ranks.map((r, i) => {
    const x = pad + (i / (ranks.length - 1)) * (w - pad * 2);
    // Invert: rank 1 = top, rank N = bottom
    const y = pad + ((r - min) / (max - min)) * (h - pad * 2);
    return `${x},${y}`;
  });
  const lastRank = ranks[ranks.length - 1];
  const firstRank = ranks[0];
  const improving = lastRank < firstRank;
  const color = improving ? '#10b981' : lastRank > firstRank ? '#f43f5e' : '#64748b';
  return (
    <svg width={w} height={h} className="inline-block">
      <polyline
        points={pts.join(' ')}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <circle cx={pts[pts.length - 1].split(',')[0]} cy={pts[pts.length - 1].split(',')[1]} r={2} fill={color} />
    </svg>
  );
}

export default function SectorsPage() {
  const [rankingData, setRankingData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [rankHistories, setRankHistories] = useState<Record<string, number[]>>({});
  const [view, setView] = useState<'rrg' | 'table'>('rrg');
  const [scopeFilter, setScopeFilter] = useState<'all' | 'level1'>('all');
  const [horizonFilter, setHorizonFilter] = useState<'tactical' | 'strategic'>('tactical');

  const fetchSectorData = async () => {
    setLoading(true);
    try {
      const hz = horizonFilter === 'strategic' ? 'strategic_260d' : 'tactical_50d';
      const res = await fetch(`/api/sectors/scores?horizon=${hz}&scope=${scopeFilter}`);
      if (res.ok) {
        const rawData = await res.json();
        const list = Array.isArray(rawData) ? rawData : (rawData.rankings || []);
        const formattedRankings = list.map((r: any, idx: number) => ({
          symbol: r.symbol || r.ticker,
          name: r.name || r.sector_name || r.ticker,
          level: r.level || 1,
          rank: r.rank || (idx + 1),
          rank_change: r.rank_change || 0,
          overall_score: Math.round(
            typeof r.overall_score === 'number' && r.overall_score > 1
              ? r.overall_score
              : typeof r.composite_score === 'number' && r.composite_score > 10
              ? r.composite_score
              : 50 + (r.composite_score || 0) * 15
          ),
          rs_ratio: r.rs_ratio,
          rs_momentum: r.rs_momentum,
          scores: r.scores || {
            momentum: Math.round(r.rs_momentum ? (r.rs_momentum - 90) * 4.5 : 50),
            relative_strength: Math.round(r.rs_ratio ? (r.rs_ratio - 90) * 4.5 : 50),
            trend: Math.round(r.rs_ratio ? (r.rs_ratio - 90) * 4.5 * 0.6 + (r.rs_momentum - 90) * 4.5 * 0.4 : 65),
            regime_fit: 82,
            risk: Math.round(100 - Math.abs((r.rs_momentum || 100) - 100) * 2.5),
          },
          classification: (r.quadrant || r.classification || 'LEADING').toUpperCase(),
          why: r.why || [],
        }));

        setRankingData({
          date: list[0]?.date || new Date().toISOString().split('T')[0],
          active_regime: 'Reflation',
          rankings: formattedRankings,
        });

        // Fetch rank history for all sectors
        const histories: Record<string, number[]> = {};
        await Promise.all(
          formattedRankings.slice(0, 15).map(async (sector: any) => {
            try {
              const hr = await fetch(`/api/sectors/scores/${sector.symbol}/history?horizon=${hz}&limit=12`);
              if (hr.ok) {
                const rows = await hr.json();
                histories[sector.symbol] = (rows || []).map((row: any) => row.rank).filter(Boolean);
              }
            } catch { /* silent */ }
          })
        );
        setRankHistories(histories);
      }
    } catch (err) {
      console.warn('Sector data fetch error, using fallback', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSectorData(); }, [horizonFilter, scopeFilter]);

  const getStatusDot = (c: string) => QUAD_COLORS[c]?.dot || 'bg-gray-400';
  const getStatusText = (c: string) => QUAD_COLORS[c]?.text || 'text-gray-400';

  const rankings: SectorItem[] = rankingData?.rankings || [];
  const level1Rankings = rankings.filter(r => !r.hasOwnProperty('level') || (r as any).level === 1);
  const activeScopeRankings = scopeFilter === 'level1' ? level1Rankings : rankings;

  const leadingSectors   = activeScopeRankings.filter(r => r.classification === 'LEADING');
  const improvingSectors = activeScopeRankings.filter(r => r.classification === 'IMPROVING');
  const weakeningSectors = activeScopeRankings.filter(r => r.classification === 'WEAKENING');
  const laggingSectors   = activeScopeRankings.filter(r => r.classification === 'LAGGING');

  // Fix 1: RRG scatter data — 2D force repulsion physics points leader lines into open space
  const rrgData = useMemo(() => {
    const list = scopeFilter === 'level1' ? level1Rankings : rankings;

    return list.map((s, i) => {
      const rx = Number(s.rs_ratio ?? 100);
      const ry = Number(s.rs_momentum ?? 100);

      let classification = s.classification;
      if (rx >= 100 && ry >= 100) classification = 'LEADING';
      else if (rx < 100 && ry >= 100) classification = 'IMPROVING';
      else if (rx >= 100 && ry < 100) classification = 'WEAKENING';
      else classification = 'LAGGING';

      // 2D force-repulsion physics to locate open surrounding space
      let vx = 0;
      let vy = 0;
      let neighbors = 0;

      for (let j = 0; j < list.length; j++) {
        if (i === j) continue;
        const jx = Number(list[j].rs_ratio ?? 100);
        const jy = Number(list[j].rs_momentum ?? 100);
        const dx = rx - jx;
        const dy = ry - jy;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 4.0) {
          neighbors++;
          const weight = 1 / (dist * dist + 0.05);
          vx += dx * weight;
          vy += dy * weight;
        }
      }

      // If no close neighbors, point outward from quadrant origin (100, 100)
      if (neighbors === 0 || (Math.abs(vx) < 0.01 && Math.abs(vy) < 0.01)) {
        vx = rx - 100;
        vy = ry - 100;
        if (Math.abs(vx) < 0.01 && Math.abs(vy) < 0.01) {
          vx = (i % 2 === 0 ? 1 : -1);
          vy = (i % 3 === 0 ? 1 : -1);
        }
      }

      const len = Math.sqrt(vx * vx + vy * vy) || 1;
      const normX = vx / len;
      const normY = vy / len;

      // Invert Y for SVG screen coordinates (higher momentum = smaller Y pixel coordinate)
      const lineLen = 22;
      const dx = normX * lineLen;
      const dy = -normY * lineLen;

      let textAnchor: 'start' | 'end' | 'middle' = 'middle';
      if (dx > 3) textAnchor = 'start';
      else if (dx < -3) textAnchor = 'end';

      return {
        symbol: s.symbol,
        name: s.name,
        rs_ratio: rx,
        rs_momentum: ry,
        overall_score: s.overall_score,
        rank: s.rank,
        classification,
        labelOffset: { dx, dy, textAnchor },
      };
    });
  }, [rankings, level1Rankings, scopeFilter, horizonFilter]);

  const xDomain = useMemo(() => {
    if (rrgData.length === 0) return [95, 105];
    const vals = rrgData.map(d => d.rs_ratio);
    const min = Math.min(...vals, 98);
    const max = Math.max(...vals, 102);
    const pad = Math.max((max - min) * 0.12, 1.5);
    return [Math.floor((min - pad) * 10) / 10, Math.ceil((max + pad) * 10) / 10];
  }, [rrgData]);

  const yDomain = useMemo(() => {
    if (rrgData.length === 0) return [95, 105];
    const vals = rrgData.map(d => d.rs_momentum);
    const min = Math.min(...vals, 98);
    const max = Math.max(...vals, 102);
    const pad = Math.max((max - min) * 0.12, 1.5);
    return [Math.floor((min - pad) * 10) / 10, Math.ceil((max + pad) * 10) / 10];
  }, [rrgData]);

  const totalSectors = level1Rankings.length;

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg-main)] text-[var(--text-main)] transition-colors">
      <Navbar asofDate={rankingData?.date} />

      <main className="flex-1 w-full px-4 sm:px-6 py-4 space-y-6">

        {/* Header */}
        <div className="space-y-4 border-b border-[var(--border-color)] pb-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="text-xs font-mono text-gray-400 uppercase tracking-wider">
                Quantitative GICS Sector Intelligence
              </div>
              <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-white tracking-tight mt-1">
                Sector Rotation Engine
              </h1>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={fetchSectorData}
                disabled={loading}
                className="text-xs font-mono text-gray-500 hover:text-[var(--text-main)] transition-colors"
              >
                {loading ? 'Refreshing...' : 'Refresh'}
              </button>
            </div>
          </div>

          <div className="flex flex-wrap gap-8 text-xs font-mono pt-1">
            <div>
              <div className="text-gray-400 text-[10px] uppercase tracking-wider">Active Macro Regime</div>
              <div className="text-xl font-bold text-slate-900 dark:text-white">
                {rankingData?.active_regime || 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-[10px] uppercase tracking-wider">As of Date</div>
              <div className="text-xl font-bold text-slate-900 dark:text-white">
                {rankingData?.date || 'N/A'}
              </div>
            </div>
          </div>
        </div>

        {/* Fix 1: RRG Chart + View Toggle */}
        <section className="space-y-4 border-b border-[var(--border-color)] pb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">
              Relative Rotation Graph (RS Ratio × RS Momentum)
            </h2>
            <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
              <div className="flex items-center space-x-1 border border-[var(--border-color)] rounded-md p-0.5 bg-[var(--bg-main)]">
                <button
                  onClick={() => setHorizonFilter('tactical')}
                  className={`px-2 py-0.5 rounded text-[10px] transition-colors ${horizonFilter === 'tactical' ? 'bg-blue-600 text-white font-bold' : 'text-gray-400 hover:text-[var(--text-main)]'}`}
                  title="50-Day Moving Average Smoothing (Tactical Sector Rotation)"
                >
                  Tactical (50D)
                </button>
                <button
                  onClick={() => setHorizonFilter('strategic')}
                  className={`px-2 py-0.5 rounded text-[10px] transition-colors ${horizonFilter === 'strategic' ? 'bg-blue-600 text-white font-bold' : 'text-gray-400 hover:text-[var(--text-main)]'}`}
                  title="260-Day (1-Year) Institutional Moving Average Smoothing (Strategic Trend)"
                >
                  Strategic (260D)
                </button>
              </div>

              <div className="flex items-center space-x-1 border border-[var(--border-color)] rounded-md p-0.5 bg-[var(--bg-main)]">
                <button
                  onClick={() => setScopeFilter('all')}
                  className={`px-2 py-0.5 rounded text-[10px] transition-colors ${scopeFilter === 'all' ? 'bg-slate-800 text-white font-bold' : 'text-gray-400 hover:text-[var(--text-main)]'}`}
                >
                  All (27)
                </button>
                <button
                  onClick={() => setScopeFilter('level1')}
                  className={`px-2 py-0.5 rounded text-[10px] transition-colors ${scopeFilter === 'level1' ? 'bg-slate-800 text-white font-bold' : 'text-gray-400 hover:text-[var(--text-main)]'}`}
                >
                  Core GICS (11)
                </button>
              </div>
              <div className="flex items-center gap-3">
                <button onClick={() => setView('rrg')} className={view === 'rrg' ? 'font-bold text-[var(--text-main)] underline underline-offset-4' : 'text-gray-500 hover:text-[var(--text-main)]'}>RRG Chart</button>
                <button onClick={() => setView('table')} className={view === 'table' ? 'font-bold text-[var(--text-main)] underline underline-offset-4' : 'text-gray-500 hover:text-[var(--text-main)]'}>Quadrant Grid</button>
              </div>
            </div>
          </div>

          {view === 'rrg' ? (
            <div className="relative border border-[var(--border-color)] rounded-xl bg-[var(--bg-main)] p-2">
              <div className="h-[420px] w-full">
                {rrgData.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs font-mono text-gray-400">
                    No RRG data available. Run sector scoring engine to populate rs_ratio / rs_momentum.
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 20, right: 35, bottom: 25, left: 35 }}>
                      <CartesianGrid strokeDasharray="2 4" stroke="var(--border-color)" opacity={0.5} />
                      <XAxis
                        dataKey="rs_ratio"
                        type="number"
                        name="RS Ratio"
                        domain={xDomain}
                        tick={{ fontSize: 10, fill: '#64748B', fontFamily: 'monospace' }}
                        stroke="#94A3B8"
                      >
                        <Label value="RS Ratio →" position="insideBottom" offset={-12} style={{ fontSize: 10, fill: '#64748B', fontFamily: 'monospace' }} />
                      </XAxis>
                      <YAxis
                        dataKey="rs_momentum"
                        type="number"
                        name="RS Momentum"
                        domain={yDomain}
                        tick={{ fontSize: 10, fill: '#64748B', fontFamily: 'monospace' }}
                        stroke="#94A3B8"
                      >
                        <Label value="RS Momentum ↑" angle={-90} position="insideLeft" offset={15} style={{ fontSize: 10, fill: '#64748B', fontFamily: 'monospace' }} />
                      </YAxis>
                      <Tooltip content={<RRGTooltip />} />
                      {/* Quadrant dividers */}
                      <ReferenceLine x={100} stroke="#64748B" strokeDasharray="4 4" strokeWidth={1} opacity={0.6} />
                      <ReferenceLine y={100} stroke="#64748B" strokeDasharray="4 4" strokeWidth={1} opacity={0.6} />
                      <Scatter
                        data={rrgData}
                        shape={<RRGDot />}
                      />
                    </ScatterChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          ) : (
            // Quadrant grid view
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              {[
                { label: 'LEADING', sectors: leadingSectors, desc: 'High RS + Rising Momentum', color: 'emerald' },
                { label: 'IMPROVING', sectors: improvingSectors, desc: 'Low RS + Rising Momentum', color: 'blue' },
                { label: 'WEAKENING', sectors: weakeningSectors, desc: 'High RS + Falling Momentum', color: 'amber' },
                { label: 'LAGGING', sectors: laggingSectors, desc: 'Low RS + Falling Momentum', color: 'rose' },
              ].map(({ label, sectors, desc, color }) => (
                <div key={label} className="border border-[var(--border-color)] rounded-xl p-4 bg-[var(--bg-main)]">
                  <div className="flex items-center justify-between mb-3 border-b border-[var(--border-color)]/50 pb-2">
                    <div className="flex items-center gap-2 font-mono font-semibold text-slate-900 dark:text-white">
                      <span className={`h-2 w-2 rounded-full bg-${color}-400`} />
                      <span>{label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400 text-[10px] font-sans">{desc}</span>
                      <span className="text-gray-400 text-[11px] font-mono">{sectors.length}</span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {sectors.length > 0 ? sectors.map(s => (
                      <Link key={s.symbol} href={`/sectors/${s.symbol}`}
                        className="px-3 py-1.5 rounded-md bg-slate-100/80 dark:bg-slate-800/50 border border-[var(--border-color)] hover:bg-slate-200/60 dark:hover:bg-slate-800 transition-all flex items-center gap-2">
                        <span className="font-bold font-mono text-slate-900 dark:text-white text-xs">{s.symbol}</span>
                        <span className="text-gray-500 font-sans text-xs">{s.name}</span>
                        <span className="font-mono text-xs font-semibold text-slate-600 dark:text-slate-400">({s.overall_score})</span>
                      </Link>
                    )) : (
                      <span className="text-gray-400 italic text-xs font-sans">None currently</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Section 2: Ranking Table — Fix 2 (sparklines) + Fix 3 (score colors) */}
        <section className="space-y-4">
          <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">
            Systematic GICS Sector Ranking Breakdown
          </h2>

          <div className="border border-[var(--border-color)] rounded-lg overflow-hidden bg-[var(--bg-main)]">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono border-collapse">
                <thead>
                  <tr className="border-b border-[var(--border-color)] text-gray-400">
                    <th className="py-3 px-4 font-mono font-normal">RANK</th>
                    <th className="py-3 px-4 font-mono font-normal">SECTOR</th>
                    <th className="py-3 px-4 text-center font-mono font-normal">SCORE</th>
                    <th className="py-3 px-4 text-center font-mono font-normal">REL STR</th>
                    <th className="py-3 px-4 text-center font-mono font-normal">MOMENTUM</th>
                    <th className="py-3 px-4 text-center font-mono font-normal">TREND</th>
                    <th className="py-3 px-4 text-center font-mono font-normal">REGIME FIT</th>
                    <th className="py-3 px-4 text-center font-mono font-normal">RISK</th>
                    <th className="py-3 px-4 text-center font-mono font-normal">RANK TREND</th>
                    <th className="py-3 px-4 text-center font-mono font-normal">STATUS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-color)]/60">
                  {(scopeFilter === 'level1' ? level1Rankings : rankings).map((item) => {
                    const rankHistory = rankHistories[item.symbol] || [];
                    return (
                      <tr key={item.symbol} className="hover:bg-slate-500/5 transition-colors">
                        <td className="py-3 px-4 font-bold text-slate-900 dark:text-white">
                          {item.rank}
                          {item.rank_change !== 0 && (
                            <span className={`ml-1 text-[10px] ${item.rank_change < 0 ? 'text-emerald-500' : 'text-rose-400'}`}>
                              {item.rank_change < 0 ? '↑' : '↓'}
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <Link href={`/sectors/${item.symbol}`} className="flex items-center space-x-2 hover:underline">
                            <span className="font-bold text-slate-900 dark:text-white">{item.symbol}</span>
                            <span className="text-gray-500 font-sans">{item.name}</span>
                          </Link>
                        </td>
                        {/* Fix 3: colored score cells */}
                        <td className={`py-3 px-4 text-center font-bold ${scoreColor(item.overall_score)}`}>
                          {item.overall_score}
                        </td>
                        <td className={`py-3 px-4 text-center ${scoreColor(item.scores?.relative_strength)}`}>
                          {item.scores?.relative_strength ?? '-'}
                        </td>
                        <td className={`py-3 px-4 text-center ${scoreColor(item.scores?.momentum)}`}>
                          {item.scores?.momentum ?? '-'}
                        </td>
                        <td className={`py-3 px-4 text-center ${scoreColor(item.scores?.trend)}`}>
                          {item.scores?.trend ?? '-'}
                        </td>
                        <td className={`py-3 px-4 text-center ${scoreColor(item.scores?.regime_fit)}`}>
                          {item.scores?.regime_fit ?? '-'}
                        </td>
                        <td className={`py-3 px-4 text-center ${scoreColor(item.scores?.risk)}`}>
                          {item.scores?.risk ?? '-'}
                        </td>
                        {/* Fix 2: rank sparkline */}
                        <td className="py-3 px-4 text-center">
                          <RankSparkline ranks={rankHistory} total={totalSectors} />
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold text-slate-900 dark:text-white">
                            <span className={`h-1.5 w-1.5 rounded-full ${getStatusDot(item.classification)}`} />
                            {item.classification}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}
