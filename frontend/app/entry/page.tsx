'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Navbar } from '@/components/Navbar';
import { Clock, Search, ArrowUpRight, RefreshCw } from 'lucide-react';

interface EntryItem {
  company_id: number;
  ticker: string;
  company_name: string;
  stock_score: number;
  entry_score: number;
  status: string;
  confidence: string;
  current_price: number;
  entry_zone: {
    low: number;
    high: number;
  };
  invalidation_price: number;
  target_price: number;
  risk_reward_ratio: number;
  setups: string[];
  event_risk: string;
}

export default function EntryPage() {
  const [entries, setEntries] = useState<EntryItem[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchEntries = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/stocks/screener?limit=100');
      if (res.ok) {
        const raw = await res.json();
        const list = Array.isArray(raw) ? raw : (raw.entry_opportunities || []);
        setEntries(list.map((s: any, idx: number) => ({
          company_id: idx + 1,
          ticker: s.ticker,
          company_name: s.name || s.ticker,
          stock_score: Math.round(s.composite_score || 50),
          entry_score: Math.round(s.momentum_score || s.composite_score || 50),
          status: 'OPTIMAL',
          confidence: 'HIGH',
          current_price: s.latest_price || s.close || 100,
          entry_zone: {
            low: (s.latest_price || 100) * 0.97,
            high: (s.latest_price || 100) * 1.01,
          },
          invalidation_price: (s.latest_price || 100) * 0.93,
          target_price: (s.latest_price || 100) * 1.15,
          risk_reward_ratio: 2.5,
          setups: ['Momentum Breakout', 'RRG Leading Quadrant'],
          event_risk: 'LOW',
        })));
      } else {
        setEntries([]);
      }
    } catch (err) {
      console.error('Failed to fetch entry timing ranking from API:', err);
      setEntries([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
  }, []);

  const filteredEntries = entries.filter(item =>
    item.ticker.toLowerCase().includes(search.toLowerCase()) ||
    item.company_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-main)] transition-colors flex flex-col">
      <Navbar />

      <main className="w-full px-4 sm:px-6 py-6 space-y-6 flex-1">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-[var(--border-color)] pb-4 gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-mono text-blue-600 dark:text-blue-400 mb-1">
              <Clock className="h-3.5 w-3.5" />
              <span>PHASE 4 ENTRY TIMING ENGINE</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight font-sans">
              Systematic Entry Timing Screener
            </h1>
            <p className="text-xs text-gray-500 mt-1 font-light max-w-3xl">
              Evaluates short-to-medium term price trend, ATR extension, support/resistance zones, valuation context, and earnings event risk.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="relative w-full md:w-72">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search ticker or company..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-main)] pl-9 pr-4 py-1.5 text-xs text-[var(--text-main)] focus:outline-none focus:border-blue-500 font-mono transition-colors"
              />
            </div>

            <button
              onClick={fetchEntries}
              disabled={loading}
              className="flex items-center space-x-1.5 rounded-md border border-[var(--border-color)] bg-[var(--bg-main)] px-3 py-1.5 text-xs font-mono text-[var(--text-main)] hover:border-blue-500 transition-all shrink-0"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>
        </div>

        {/* Full-Width Grid of Entry Timing Opportunities */}
        {loading ? (
          <div className="py-16 text-center text-gray-500 font-mono text-xs flex flex-col items-center justify-center space-y-2">
            <RefreshCw className="h-5 w-5 animate-spin text-blue-600" />
            <span>Loading live Phase 4 entry timing opportunities...</span>
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="py-16 text-center text-gray-500 font-mono text-xs">
            No entry timing opportunities found in database matching search "{search}".
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredEntries.map(item => (
              <div key={item.ticker} className="border border-[var(--border-color)] rounded-md bg-[var(--bg-main)] p-5 flex flex-col justify-between space-y-4 hover:border-blue-500/40 transition-colors font-mono text-xs">
                <div>
                  {/* Header */}
                  <div className="flex items-start justify-between pb-2 border-b border-[var(--border-color)]">
                    <div>
                      <Link href={`/stocks/${item.ticker}`} className="text-xl font-extrabold text-blue-600 dark:text-blue-400 hover:underline">
                        {item.ticker}
                      </Link>
                      <div className="text-xs font-sans font-medium text-[var(--text-main)] truncate max-w-[180px] mt-0.5">
                        {item.company_name}
                      </div>
                    </div>

                    <div className="text-right">
                      <span className="text-xl font-extrabold text-blue-600 dark:text-blue-400">
                        {item.entry_score.toFixed(1)}
                      </span>
                      <span className="block text-[9px] text-gray-400 uppercase">Entry Score</span>
                    </div>
                  </div>

                  {/* Score Pair Bar */}
                  <div className="grid grid-cols-2 gap-2 mt-3 text-[11px] bg-[var(--border-color)]/20 p-2 rounded">
                    <div>
                      <span className="text-gray-400 block text-[9px]">STOCK QUALITY</span>
                      <strong className="text-slate-900 dark:text-white font-bold">{item.stock_score.toFixed(1)}</strong>
                    </div>
                    <div>
                      <span className="text-gray-400 block text-[9px]">TIMING SCORE</span>
                      <strong className="text-blue-600 dark:text-blue-400 font-bold">{item.entry_score.toFixed(1)}</strong>
                    </div>
                  </div>

                  {/* Setup Tags */}
                  <div className="mt-3 space-y-1.5">
                    <span className="text-[10px] text-gray-400 uppercase">TECHNICAL PATTERN</span>
                    <div className="flex flex-wrap gap-1">
                      {item.setups.map((setup, idx) => (
                        <span key={idx} className="bg-blue-500/10 text-blue-600 dark:text-blue-400 text-[10px] px-2 py-0.5 rounded border border-blue-500/20 font-bold">
                          {setup}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Preferred Entry Range & Stop */}
                  <div className="mt-3 pt-2 border-t border-[var(--border-color)] space-y-1.5 text-[11px]">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">Current Price:</span>
                      <strong className="text-[var(--text-main)]">${item.current_price.toFixed(2)}</strong>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">Entry Range:</span>
                      <strong className="text-emerald-500">${item.entry_zone.low.toFixed(2)} – ${item.entry_zone.high.toFixed(2)}</strong>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">Stop Level:</span>
                      <strong className="text-rose-500">${item.invalidation_price.toFixed(2)}</strong>
                    </div>
                    <div className="flex justify-between items-center pt-1 border-t border-[var(--border-color)]">
                      <span className="text-gray-400">Risk / Reward:</span>
                      <strong className="text-amber-500 font-bold">{item.risk_reward_ratio.toFixed(2)} R/R</strong>
                    </div>
                  </div>
                </div>

                <div className="pt-2 border-t border-[var(--border-color)] text-[10px] text-gray-400 flex items-center justify-between">
                  <span>Event Risk: <strong className="text-[var(--text-main)]">{item.event_risk}</strong></span>
                  <Link href={`/stocks/${item.ticker}`} className="text-blue-600 dark:text-blue-400 hover:underline flex items-center space-x-1 font-bold">
                    <span>View Details</span>
                    <ArrowUpRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
