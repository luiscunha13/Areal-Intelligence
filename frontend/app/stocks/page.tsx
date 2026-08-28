'use client';

import React, { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import { Navbar } from '@/components/Navbar';
import { Search, RefreshCw, Layers, ShieldCheck, Zap, TrendingUp } from 'lucide-react';

interface StockRankItem {
  company_id: number;
  ticker: string;
  company_name: string;
  sector_id: number;
  sector_name?: string;
  market_cap?: number;
  close_price?: number;
  rank: number;
  overall_score: number;
  quality_score?: number;
  growth_score?: number;
  valuation_score?: number;
  earnings_score?: number;
  technical_score?: number;
  relative_strength_score?: number;
  revenue?: number;
  net_income?: number;
  eps?: number;
  pe_ratio?: number;
  revenue_growth_yoy?: number;
  gross_margin?: number;
  roic?: number;
}

interface SectorRankItem {
  symbol: string;
  name: string;
  rank: number;
  overall_score: number;
  classification?: string;
}

const SECTOR_MAP: Record<number, string> = {
  1: 'Technology',
  2: 'Healthcare',
  3: 'Financials',
  4: 'Consumer Cyclical',
  5: 'Communication',
  6: 'Industrials',
  7: 'Consumer Staples',
  8: 'Energy',
  9: 'Utilities',
  10: 'Real Estate',
  11: 'Basic Materials',
};

const CompanyLogo: React.FC<{ ticker: string; className?: string }> = ({
  ticker,
  className = "w-6 h-6",
}) => {
  const [error, setError] = useState(false);
  const logoUrl = `https://assets.parqet.com/logos/symbol/${ticker}?format=png`;

  if (error || !ticker) {
    return (
      <div className={`${className} rounded-full bg-blue-600/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-mono font-bold flex items-center justify-center text-[10px] shrink-0`}>
        {ticker.slice(0, 2)}
      </div>
    );
  }

  return (
    <img
      src={logoUrl}
      alt={`${ticker} logo`}
      onError={() => setError(true)}
      className={`${className} rounded-full object-contain bg-white dark:bg-slate-900 border border-[var(--border-color)] p-0.5 shrink-0`}
    />
  );
};

export default function StocksPage() {
  const [rankings, setRankings] = useState<StockRankItem[]>([]);
  const [sectorRankings, setSectorRankings] = useState<SectorRankItem[]>([]);
  const [activeRegime, setActiveRegime] = useState<string>('Goldilocks (Restrictive policy)');
  const [search, setSearch] = useState('');
  const [selectedSector, setSelectedSector] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  const fetchMacroAndSectors = async () => {
    try {
      const [rRegime, rSectors] = await Promise.all([
        fetch('http://127.0.0.1:8000/api/regime/current').then(res => res.ok ? res.json() : null),
        fetch('http://127.0.0.1:8000/api/sectors/ranking').then(res => res.ok ? res.json() : null)
      ]);

      if (rRegime && rRegime.regime) {
        setActiveRegime(rRegime.regime);
      }
      if (rSectors && rSectors.rankings) {
        setSectorRankings(rSectors.rankings);
      }
    } catch (err) {
      console.error('Error fetching macro/sector headers:', err);
    }
  };

  const fetchRankings = async (queryStr = search) => {
    setLoading(true);
    try {
      const url = queryStr.trim()
        ? `http://127.0.0.1:8000/api/companies/rankings?search=${encodeURIComponent(queryStr.trim())}&limit=2000`
        : `http://127.0.0.1:8000/api/companies/rankings?limit=2000`;

      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (data && data.rankings) {
          setRankings(data.rankings);
        } else {
          setRankings([]);
        }
      } else {
        setRankings([]);
      }
    } catch (err) {
      console.error('Failed to fetch stock rankings from API:', err);
      setRankings([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMacroAndSectors();
  }, []);

  // Trigger search fetch with a short debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchRankings(search);
    }, 250);
    return () => clearTimeout(timer);
  }, [search]);

  const filteredRankings = useMemo(() => {
    return rankings.filter((item) => {
      const sectorName = (item.sector_name || SECTOR_MAP[item.sector_id] || '').toLowerCase();
      const matchesSector = selectedSector === 'all' || sectorName.includes(selectedSector.toLowerCase());
      return matchesSector;
    });
  }, [rankings, selectedSector]);

  const formatCurrencyBillions = (val?: number) => {
    if (val === undefined || val === null || val === 0) return '-';
    if (Math.abs(val) >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
    if (Math.abs(val) >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
    if (Math.abs(val) >= 1e6) return `$${(val / 1e6).toFixed(1)}M`;
    return `$${val.toFixed(2)}`;
  };

  // Helper map to pull live sector scores for quick pills
  const sectorScoreMap = useMemo(() => {
    const map: Record<string, number> = {};
    sectorRankings.forEach(s => {
      map[s.name.toLowerCase()] = s.overall_score;
    });
    return map;
  }, [sectorRankings]);

  return (
    <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-main)] transition-colors flex flex-col">
      <Navbar />

      <main className="w-full px-4 sm:px-6 py-6 space-y-6 flex-1">
        {/* Institutional Macro & Sector Synergy Top Header Banner */}
        <div className="p-4 rounded-md border border-blue-500/20 bg-blue-500/5 space-y-3 font-mono text-xs">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-blue-500/10 pb-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] uppercase text-gray-400 font-bold">ACTIVE MACRO REGIME:</span>
              <span className="px-2.5 py-0.5 rounded font-extrabold bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-500/30">
                {activeRegime}
              </span>
              <span className="text-[10px] uppercase text-gray-400 font-bold ml-2">METHODOLOGY:</span>
              <span className="px-2.5 py-0.5 rounded font-bold bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                v2.0-PIT (Z-Score Cohort Normalized)
              </span>
            </div>

            <div className="flex items-center space-x-3 text-[11px]">
              <span className="flex items-center space-x-1 text-emerald-500">
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>Zero-Null Imputed Integrity</span>
              </span>
              <span className="flex items-center space-x-1 text-blue-500">
                <Zap className="h-3.5 w-3.5" />
                <span>Materialized Sub-Sec Cache</span>
              </span>
            </div>
          </div>

          {/* Sector Rotation Leadership Highlights */}
          {sectorRankings.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px]">
              <span className="text-gray-400 uppercase text-[10px] font-bold">SECTOR LEADERSHIP:</span>
              {sectorRankings.slice(0, 4).map((sec) => (
                <span
                  key={sec.symbol}
                  className="px-2 py-0.5 rounded bg-[var(--bg-main)] border border-[var(--border-color)] text-slate-800 dark:text-gray-200"
                >
                  <strong className="text-blue-600 dark:text-blue-400">{sec.name}:</strong> {sec.overall_score.toFixed(1)}/100
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Header & Controls */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-[var(--border-color)] pb-4 gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs font-mono text-blue-600 dark:text-blue-400 mb-1">
              <Layers className="h-3.5 w-3.5" />
              <span>POINT-IN-TIME MARKET SCREENER (10,423 EQUITIES IN DATABASE)</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight font-sans">
              Global Equities Screener & Factor Rankings
            </h1>
            <p className="text-xs text-gray-500 mt-1 font-light max-w-3xl">
              Cross-sectionally normalized Z-score rankings combined with live sector momentum and macro regime sensitivity.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="relative w-full md:w-80">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search 10,423 tickers (e.g. NVDA, VLO, MU, AAPL)..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-main)] pl-9 pr-4 py-1.5 text-xs text-[var(--text-main)] focus:outline-none focus:border-blue-500 font-mono transition-colors"
              />
            </div>

            <button
              onClick={() => fetchRankings(search)}
              disabled={loading}
              className="flex items-center space-x-1.5 rounded-md border border-[var(--border-color)] bg-[var(--bg-main)] px-3 py-1.5 text-xs font-mono text-[var(--text-main)] hover:border-blue-500 transition-all shrink-0"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>
        </div>

        {/* Sector Quick Filter Pills with Dynamic Sector Scores */}
        <div className="flex flex-wrap gap-2 text-xs font-mono">
          {['all', 'technology', 'healthcare', 'financials', 'energy', 'industrials', 'materials', 'utilities'].map((secKey) => {
            const scoreVal = sectorScoreMap[secKey];
            return (
              <button
                key={secKey}
                onClick={() => setSelectedSector(secKey)}
                className={`px-3 py-1 rounded transition-all uppercase flex items-center space-x-1 border ${
                  selectedSector === secKey
                    ? 'font-bold bg-blue-600 text-white border-blue-600 shadow-sm'
                    : 'bg-[var(--bg-main)] text-gray-500 border-[var(--border-color)] hover:border-blue-500 hover:text-[var(--text-main)]'
                }`}
              >
                <span>{secKey}</span>
                {scoreVal !== undefined && (
                  <span className="text-[10px] opacity-80 font-mono">({scoreVal.toFixed(0)})</span>
                )}
              </button>
            );
          })}
        </div>

        {/* Full-Width High-Density Stock Fundamental Table */}
        <div className="border border-[var(--border-color)] rounded-md overflow-hidden bg-[var(--bg-main)]">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[var(--bg-main)] border-b border-[var(--border-color)] text-gray-400 uppercase text-[10px]">
                <tr>
                  <th className="py-3 px-4 text-center w-12">Rank</th>
                  <th className="py-3 px-4">Company</th>
                  <th className="py-3 px-4">Sector</th>
                  <th className="py-3 px-4 text-right">Price</th>
                  <th className="py-3 px-4 text-right">Market Cap</th>
                  <th className="py-3 px-4 text-right">Revenue</th>
                  <th className="py-3 px-4 text-right">Net Income</th>
                  <th className="py-3 px-4 text-right">P/E Ratio</th>
                  <th className="py-3 px-4 text-right">YoY Growth</th>
                  <th className="py-3 px-4 text-right">Gross Margin</th>
                  <th className="py-3 px-4 text-right">Overall Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-color)]">
                {loading ? (
                  <tr>
                    <td colSpan={11} className="py-12 text-center text-gray-500 font-mono">
                      <div className="inline-flex items-center space-x-2">
                        <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                        <span>Fetching materialized snapshots across 10,423 equities...</span>
                      </div>
                    </td>
                  </tr>
                ) : filteredRankings.length === 0 ? (
                  <tr>
                    <td colSpan={11} className="py-12 text-center text-gray-500 font-mono">
                      No companies found in database matching query "{search}".
                    </td>
                  </tr>
                ) : (
                  filteredRankings.map((stock) => (
                    <tr
                      key={stock.ticker}
                      className="hover:bg-[var(--border-color)]/20 transition-colors"
                    >
                      <td className="py-2.5 px-4 text-center font-bold text-gray-400">
                        #{stock.rank}
                      </td>
                      <td className="py-2.5 px-4">
                        <Link href={`/stocks/${stock.ticker}`} className="flex items-center space-x-2.5 hover:underline group">
                          <CompanyLogo ticker={stock.ticker} />
                          <div>
                            <span className="font-bold text-blue-600 dark:text-blue-400 block group-hover:underline">
                              {stock.ticker}
                            </span>
                            <span className="text-[11px] font-sans font-normal text-[var(--text-main)] block truncate max-w-[200px]">
                              {stock.company_name}
                            </span>
                          </div>
                        </Link>
                      </td>
                      <td className="py-2.5 px-4 text-gray-500 text-[11px]">
                        {stock.sector_name || SECTOR_MAP[stock.sector_id] || 'General'}
                      </td>
                      <td className="py-2.5 px-4 text-right font-bold text-slate-900 dark:text-white">
                        {stock.close_price ? `$${stock.close_price.toFixed(2)}` : '-'}
                      </td>
                      <td className="py-2.5 px-4 text-right text-gray-600 dark:text-gray-300">
                        {formatCurrencyBillions(stock.market_cap)}
                      </td>
                      <td className="py-2.5 px-4 text-right text-gray-600 dark:text-gray-300">
                        {formatCurrencyBillions(stock.revenue)}
                      </td>
                      <td className="py-2.5 px-4 text-right text-gray-600 dark:text-gray-300">
                        {formatCurrencyBillions(stock.net_income)}
                      </td>
                      <td className="py-2.5 px-4 text-right text-gray-600 dark:text-gray-300">
                        {stock.pe_ratio ? `${stock.pe_ratio.toFixed(1)}x` : '-'}
                      </td>
                      <td className="py-2.5 px-4 text-right">
                        {stock.revenue_growth_yoy !== undefined && stock.revenue_growth_yoy !== null ? (
                          <span className={`font-bold ${stock.revenue_growth_yoy >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                            {stock.revenue_growth_yoy >= 0 ? '+' : ''}{stock.revenue_growth_yoy.toFixed(1)}%
                          </span>
                        ) : '-'}
                      </td>
                      <td className="py-2.5 px-4 text-right text-gray-600 dark:text-gray-300">
                        {stock.gross_margin ? `${stock.gross_margin.toFixed(1)}%` : '-'}
                      </td>
                      <td className="py-2.5 px-4 text-right">
                        <Link href={`/stocks/${stock.ticker}`}>
                          <span
                            className={`inline-block px-2.5 py-0.5 rounded text-xs font-extrabold ${
                              stock.overall_score >= 65
                                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                                : stock.overall_score >= 55
                                ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20'
                                : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                            }`}
                          >
                            {stock.overall_score ? stock.overall_score.toFixed(1) : '-'}
                          </span>
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
