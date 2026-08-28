'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { Navbar } from '../../components/Navbar';

// ── Types ────────────────────────────────────────────────────────
interface EtfScore {
  ticker: string;
  date: string;
  name: string;
  category: string;
  sub_category: string;
  benchmark: string;
  expense_ratio: number;
  composite_score: number;
  rank_overall: number;
  rank_category: number;
  momentum_1m: number;
  momentum_3m: number;
  momentum_6m: number;
  momentum_12m: number;
  sharpe_1y: number;
  volatility_1y: number;
  latest_price: number;
}

interface Category {
  category: string;
  count: number;
}

const CATEGORY_LABELS: Record<string, string> = {
  all: 'All ETFs',
  sector: 'Sector',
  factor: 'Factor / Style',
  fixed_income: 'Fixed Income',
  international: 'International',
  commodity: 'Commodity',
  real_estate: 'Real Estate',
  thematic: 'Thematic',
  volatility: 'Volatility',
  multi_asset: 'Multi-Asset',
};

const CLASSIFICATION_COLORS: Record<string, string> = {
  strong_buy: 'text-emerald-400',
  buy: 'text-green-400',
  neutral: 'text-slate-400',
  underperform: 'text-amber-400',
  avoid: 'text-red-400',
};

const CLASSIFICATION_LABELS: Record<string, string> = {
  strong_buy: 'Strong Buy',
  buy: 'Buy',
  neutral: 'Neutral',
  underperform: 'Underperform',
  avoid: 'Avoid',
};

function classifyScore(score: number): string {
  if (score >= 80) return 'strong_buy';
  if (score >= 60) return 'buy';
  if (score >= 40) return 'neutral';
  if (score >= 20) return 'underperform';
  return 'avoid';
}

function fmt(val: number | null | undefined, decimals = 2, suffix = ''): string {
  if (val == null) return '—';
  const sign = val > 0 ? '+' : '';
  return `${sign}${val.toFixed(decimals)}${suffix}`;
}

function ScoreBar({ score }: { score: number }) {
  const w = Math.min(100, Math.max(0, score));
  const color = score >= 75 ? '#34d399' : score >= 50 ? '#60a5fa' : score >= 25 ? '#fbbf24' : '#f87171';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-[var(--border-color)] rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${w}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs font-mono text-[var(--text-secondary)] w-8 text-right">{score?.toFixed(0)}</span>
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────
export default function EtfsPage() {
  const [scores, setScores] = useState<EtfScore[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'rank' | 'momentum_3m' | 'sharpe_1y' | 'volatility_1y'>('rank');
  const [loading, setLoading] = useState(true);
  const [asOfDate, setAsOfDate] = useState<string>('');

  const fetchScores = useCallback(async (category: string) => {
    setLoading(true);
    try {
      const catParam = category !== 'all' ? `&category=${category}` : '';
      const res = await fetch(`/api/etfs/scores?limit=200${catParam}`);
      const data: EtfScore[] = await res.json();
      setScores(data);
      if (data.length > 0) setAsOfDate(data[0].date);
    } catch (e) {
      console.error('Failed to fetch ETF scores', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch('/api/etfs/categories')
      .then(r => r.json())
      .then(setCategories)
      .catch(console.error);
  }, []);

  useEffect(() => {
    fetchScores(selectedCategory);
  }, [selectedCategory, fetchScores]);

  const sorted = [...scores].sort((a, b) => {
    if (sortBy === 'rank') return (a.rank_overall ?? 999) - (b.rank_overall ?? 999);
    if (sortBy === 'momentum_3m') return (b.momentum_3m ?? -999) - (a.momentum_3m ?? -999);
    if (sortBy === 'sharpe_1y') return (b.sharpe_1y ?? -999) - (a.sharpe_1y ?? -999);
    if (sortBy === 'volatility_1y') return (a.volatility_1y ?? 999) - (b.volatility_1y ?? 999);
    return 0;
  });

  // Summary cards
  const topEtfs = scores.filter(s => s.composite_score >= 80).length;
  const avgScore = scores.length ? scores.reduce((s, e) => s + (e.composite_score ?? 0), 0) / scores.length : 0;

  return (
    <div className="flex min-h-screen flex-col bg-[var(--bg-main)] text-[var(--text-main)] transition-colors">
      <Navbar asofDate={asOfDate} />

      <main className="flex-1 w-full px-4 py-6 sm:px-6 space-y-6">

        {/* ── Header ── */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold tracking-tight text-[var(--text-main)]">ETF Analysis</h1>
            <p className="text-xs text-[var(--text-secondary)] mt-0.5">
              {scores.length} ETFs · Multi-factor momentum & risk-adjusted scoring
              {asOfDate && <span className="ml-2 font-mono">As of {asOfDate}</span>}
            </p>
          </div>
        </div>

        {/* ── Summary Cards ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Universe', value: scores.length.toString(), sub: 'active ETFs' },
            { label: 'Strong Buy', value: topEtfs.toString(), sub: 'score ≥ 80' },
            { label: 'Avg Score', value: avgScore.toFixed(1), sub: 'composite' },
            { label: 'Categories', value: categories.length.toString(), sub: 'asset classes' },
          ].map(card => (
            <div key={card.label} className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-3">
              <p className="text-xs text-[var(--text-secondary)]">{card.label}</p>
              <p className="text-xl font-bold font-mono text-[var(--text-main)] mt-1">{card.value}</p>
              <p className="text-xs text-[var(--text-secondary)]">{card.sub}</p>
            </div>
          ))}
        </div>

        {/* ── Controls ── */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Category filter */}
          <div className="flex flex-wrap gap-1">
            {[{ category: 'all', count: scores.length }, ...categories].map(c => (
              <button
                key={c.category}
                onClick={() => setSelectedCategory(c.category)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  selectedCategory === c.category
                    ? 'bg-blue-600 text-white'
                    : 'bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-main)]'
                }`}
              >
                {CATEGORY_LABELS[c.category] ?? c.category}
              </button>
            ))}
          </div>

          {/* Sort */}
          <div className="ml-auto flex items-center gap-1 text-xs text-[var(--text-secondary)]">
            <span>Sort:</span>
            {(['rank', 'momentum_3m', 'sharpe_1y', 'volatility_1y'] as const).map(s => (
              <button
                key={s}
                onClick={() => setSortBy(s)}
                className={`px-2 py-1 rounded transition-colors ${
                  sortBy === s ? 'text-[var(--text-main)] font-semibold' : 'hover:text-[var(--text-main)]'
                }`}
              >
                {s === 'rank' ? 'Score' : s === 'momentum_3m' ? '3M Return' : s === 'sharpe_1y' ? 'Sharpe' : 'Vol'}
              </button>
            ))}
          </div>
        </div>

        {/* ── Table ── */}
        <div className="rounded-lg border border-[var(--border-color)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[var(--border-color)] bg-[var(--bg-card)]">
                  {['#', 'Ticker', 'Name', 'Category', 'Score', '1M', '3M', '6M', '12M', 'Sharpe', 'Vol', 'Price', 'ER'].map(h => (
                    <th key={h} className="px-3 py-2.5 text-left font-medium text-[var(--text-secondary)] whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={13} className="px-3 py-8 text-center text-[var(--text-secondary)]">Loading…</td></tr>
                ) : sorted.length === 0 ? (
                  <tr><td colSpan={13} className="px-3 py-8 text-center text-[var(--text-secondary)]">No data available yet — run the scoring pipeline first.</td></tr>
                ) : sorted.map((etf, i) => {
                  const cls = classifyScore(etf.composite_score ?? 0);
                  return (
                    <tr key={etf.ticker} className="border-b border-[var(--border-color)] hover:bg-[var(--bg-card)] transition-colors">
                      <td className="px-3 py-2 font-mono text-[var(--text-secondary)]">{etf.rank_overall ?? i + 1}</td>
                      <td className="px-3 py-2">
                        <span className="font-mono font-semibold text-[var(--text-main)]">{etf.ticker}</span>
                      </td>
                      <td className="px-3 py-2 text-[var(--text-secondary)] max-w-[180px] truncate" title={etf.name}>
                        {etf.name}
                      </td>
                      <td className="px-3 py-2">
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-[var(--border-color)] text-[var(--text-secondary)]">
                          {CATEGORY_LABELS[etf.category] ?? etf.category}
                        </span>
                      </td>
                      <td className="px-3 py-2 min-w-[100px]">
                        <ScoreBar score={etf.composite_score ?? 0} />
                      </td>
                      <td className={`px-3 py-2 font-mono ${(etf.momentum_1m ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {fmt(etf.momentum_1m, 1, '%')}
                      </td>
                      <td className={`px-3 py-2 font-mono ${(etf.momentum_3m ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {fmt(etf.momentum_3m, 1, '%')}
                      </td>
                      <td className={`px-3 py-2 font-mono ${(etf.momentum_6m ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {fmt(etf.momentum_6m, 1, '%')}
                      </td>
                      <td className={`px-3 py-2 font-mono ${(etf.momentum_12m ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {fmt(etf.momentum_12m, 1, '%')}
                      </td>
                      <td className="px-3 py-2 font-mono text-[var(--text-main)]">
                        {fmt(etf.sharpe_1y, 2)}
                      </td>
                      <td className="px-3 py-2 font-mono text-[var(--text-secondary)]">
                        {etf.volatility_1y != null ? `${etf.volatility_1y.toFixed(1)}%` : '—'}
                      </td>
                      <td className="px-3 py-2 font-mono text-[var(--text-main)]">
                        {etf.latest_price != null ? `$${etf.latest_price.toFixed(2)}` : '—'}
                      </td>
                      <td className="px-3 py-2 font-mono text-[var(--text-secondary)]">
                        {etf.expense_ratio != null ? `${(etf.expense_ratio * 100).toFixed(2)}%` : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

      </main>
    </div>
  );
}
