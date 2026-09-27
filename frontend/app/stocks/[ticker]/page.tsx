'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { Navbar } from '@/components/Navbar';
import { ArrowLeft, Clock, CheckCircle2, DollarSign, RefreshCw, PieChart } from 'lucide-react';

interface FinancialMetricDetail {
  period_end: string;
  period_type: string;
  revenue?: number;
  gross_profit?: number;
  operating_income?: number;
  ebitda?: number;
  net_income?: number;
  eps?: number;
  cash?: number;
  total_debt?: number;
  total_assets?: number;
  equity?: number;
  operating_cash_flow?: number;
  free_cash_flow?: number;
  revenue_growth_yoy?: number;
  eps_growth_yoy?: number;
  roic?: number;
  roe?: number;
  gross_margin?: number;
  operating_margin?: number;
  fcf_margin?: number;
  pe_ratio?: number;
  forward_pe?: number;
  ev_to_ebitda?: number;
  price_to_fcf?: number;
  eps_surprise_pct?: number;
}

interface EntryDetail {
  entry_score: number;
  status: string;
  confidence: string;
  subscores: {
    trend_score: number;
    momentum_score: number;
    extension_score: number;
    support_resistance_score: number;
    valuation_context_score: number;
    event_risk_score: number;
  };
  entry_zone: {
    current_price: number;
    entry_zone_low: number;
    entry_zone_high: number;
    invalidation_price: number;
    target_price: number;
    risk_reward_ratio: number;
  };
  setups: Array<{ setup_type: string; signal_strength: number; description: string }>;
  event_risk: string;
}

interface StockDetail {
  id: number;
  ticker: string;
  company_name: string;
  legal_name?: string;
  exchange: string;
  country: string;
  currency: string;
  market_cap?: number;
  sector_id?: number;
  sector_name?: string;
  sector_score?: number;
  active_regime?: string;
  macro_fit_score?: number;
  composite_candidate_score?: number;
  candidate_category?: string;
  thesis_explanations?: string[];
  industry?: {
    name: string;
    description?: string;
  };
  latest_price?: {
    close: number;
    adjusted_close: number;
    date: string;
  };
  latest_score?: {
    overall_score: number;
    rank?: number;
    quality_score?: number;
    growth_score?: number;
    valuation_score?: number;
    earnings_score?: number;
    technical_score?: number;
    relative_strength_score?: number;
  };
  latest_financials?: FinancialMetricDetail;
}

const CompanyLogo: React.FC<{ ticker: string; className?: string }> = ({
  ticker,
  className = "w-8 h-8",
}) => {
  const [error, setError] = useState(false);
  const logoUrl = `https://assets.parqet.com/logos/symbol/${ticker}?format=png`;

  if (error || !ticker) {
    return (
      <div className={`${className} rounded-full bg-blue-600/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-mono font-bold flex items-center justify-center text-xs shrink-0`}>
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

export default function StockDetailPage() {
  const params = useParams();
  const ticker = (params?.ticker as string || '').toUpperCase();

  const [stock, setStock] = useState<StockDetail | null>(null);
  const [entryDetail, setEntryDetail] = useState<EntryDetail | null>(null);
  const [activeMenuTab, setActiveMenuTab] = useState<'financials' | 'scores' | 'timing'>('financials');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ticker) return;

    setLoading(true);
    const p1 = fetch(`http://127.0.0.1:8000/api/companies/${ticker}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.ticker) {
          setStock(data);
        } else {
          setStock(null);
        }
      })
      .catch((err) => {
        console.error(`Error loading stock ${ticker}:`, err);
        setStock(null);
      });

    const p2 = fetch(`http://127.0.0.1:8000/api/entry/company/${ticker}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.entry_score) {
          setEntryDetail(data);
        } else {
          setEntryDetail(null);
        }
      })
      .catch((err) => {
        console.error(`Error loading entry timing for ${ticker}:`, err);
        setEntryDetail(null);
      });

    Promise.allSettled([p1, p2]).finally(() => setLoading(false));
  }, [ticker]);

  const formatCurrencyBillions = (val?: number) => {
    if (val === undefined || val === null || val === 0) return '-';
    if (Math.abs(val) >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
    if (Math.abs(val) >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
    if (Math.abs(val) >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
    return `$${val.toFixed(2)}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-main)] transition-colors flex flex-col">
        <Navbar />
        <main className="w-full px-4 sm:px-6 py-16 text-center font-mono text-xs text-gray-500 flex-1 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
          <span>Fetching live profile and financial statements for {ticker}...</span>
        </main>
      </div>
    );
  }

  if (!stock) {
    return (
      <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-main)] transition-colors flex flex-col">
        <Navbar />
        <main className="w-full px-4 sm:px-6 py-16 text-center font-mono text-xs text-gray-500 flex-1 flex flex-col items-center justify-center space-y-4">
          <p>No equity records found in database for ticker <strong className="text-blue-600 dark:text-blue-400">{ticker}</strong>.</p>
          <Link
            href="/stocks"
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded border border-[var(--border-color)] text-xs text-[var(--text-main)] hover:border-blue-500 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Return to Stock Screener</span>
          </Link>
        </main>
      </div>
    );
  }

  const sc = stock.latest_score;
  const fin = stock.latest_financials;
  const closePrice = stock.latest_price?.close || entryDetail?.entry_zone?.current_price;

  return (
    <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-main)] transition-colors flex flex-col">
      <Navbar />

      <main className="w-full px-4 sm:px-6 py-6 space-y-6 flex-1">
        {/* Navigation & Stock Header */}
        <div className="space-y-4">
          <Link
            href="/stocks"
            className="inline-flex items-center space-x-1.5 text-xs text-blue-600 dark:text-blue-400 hover:underline font-mono"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>← Back to Stock Screener</span>
          </Link>

          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[var(--border-color)] pb-6">
            <div className="flex items-start space-x-4">
              <CompanyLogo ticker={stock.ticker} className="w-12 h-12 mt-1" />
              <div>
                <div className="flex items-center space-x-3">
                  <span className="text-3xl font-extrabold font-mono text-blue-600 dark:text-blue-400">
                    {stock.ticker}
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs font-mono bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                    {stock.exchange}
                  </span>
                  {closePrice && (
                    <span className="text-2xl font-bold font-mono text-emerald-500 ml-2">
                      ${closePrice.toFixed(2)}
                    </span>
                  )}
                  {stock.industry?.name && (
                    <span className="text-xs font-mono text-gray-400 hidden sm:inline">
                      • {stock.industry.name}
                    </span>
                  )}
                </div>

                <h1 className="text-2xl font-bold font-sans mt-1 text-slate-900 dark:text-white">
                  {stock.company_name}
                </h1>

                <p className="text-xs text-gray-500 font-mono mt-1">
                  Market Cap:{' '}
                  <strong className="text-[var(--text-main)]">
                    {formatCurrencyBillions(stock.market_cap)}
                  </strong>{' '}
                  • Currency: {stock.currency} • Country: {stock.country}
                </p>
              </div>
            </div>

            {/* Overall Stock Score Circle */}
            {sc && (
              <div className="flex items-center space-x-6 py-2 px-4 border border-[var(--border-color)] rounded-md font-mono text-xs bg-[var(--bg-main)]">
                <div>
                  <div className="text-gray-400 text-[10px]">OVERALL SCORE</div>
                  <div className="text-2xl font-extrabold text-blue-600 dark:text-blue-400">
                    {sc.overall_score.toFixed(1)}
                  </div>
                </div>
                {sc.rank && (
                  <div className="border-l border-[var(--border-color)] pl-6">
                    <div className="text-gray-400 text-[10px]">MARKET RANK</div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white">
                      #{sc.rank}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Macro Regime & Sector Synergy Banner */}
          {stock.active_regime && (
            <div className="p-4 rounded border border-blue-500/20 bg-blue-500/5 space-y-3 font-mono text-xs">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-blue-500/10 pb-2.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[10px] uppercase text-gray-400">ACTIVE REGIME:</span>
                  <span className="px-2.5 py-0.5 rounded font-bold bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-500/30">
                    {stock.active_regime}
                  </span>
                  <span className="text-[10px] uppercase text-gray-400 ml-2">SECTOR:</span>
                  <span className="px-2.5 py-0.5 rounded font-bold bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                    {stock.sector_name || 'General'} ({stock.sector_score?.toFixed(1)}/100)
                  </span>
                </div>

                <div className="flex items-center space-x-3">
                  <span className="text-gray-400">
                    Macro Fit: <strong className="text-blue-600 dark:text-blue-400">{stock.macro_fit_score?.toFixed(1)}/100</strong>
                  </span>
                  <span className="px-3 py-1 rounded text-xs font-extrabold uppercase bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                    {stock.composite_candidate_score?.toFixed(1)} / 100 — {stock.candidate_category}
                  </span>
                </div>
              </div>

              {stock.thesis_explanations && stock.thesis_explanations.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[10px] uppercase text-gray-400 font-bold block">QUANTITATIVE THESIS DRIVERS:</span>
                  <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-slate-700 dark:text-gray-300 font-sans">
                    {stock.thesis_explanations.map((exp, idx) => (
                      <li key={idx} className="flex items-start space-x-1.5 text-xs">
                        <span className="text-blue-500 font-mono font-bold">•</span>
                        <span>{exp}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Tabbed Menu Navigation Bar */}
        <div className="flex items-center space-x-6 border-b border-[var(--border-color)] pb-3 font-mono text-xs">
          <button
            onClick={() => setActiveMenuTab('financials')}
            className={`flex items-center space-x-1.5 transition-colors ${
              activeMenuTab === 'financials'
                ? 'font-bold text-[var(--text-main)] underline underline-offset-8 decoration-2 decoration-blue-600'
                : 'text-gray-500 hover:text-[var(--text-main)]'
            }`}
          >
            <DollarSign className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
            <span>Real Financial Data & Statements</span>
          </button>

          <button
            onClick={() => setActiveMenuTab('scores')}
            className={`flex items-center space-x-1.5 transition-colors ${
              activeMenuTab === 'scores'
                ? 'font-bold text-[var(--text-main)] underline underline-offset-8 decoration-2 decoration-blue-600'
                : 'text-gray-500 hover:text-[var(--text-main)]'
            }`}
          >
            <PieChart className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
            <span>Multi-Factor Quantitative Scores</span>
          </button>

          <button
            onClick={() => setActiveMenuTab('timing')}
            className={`flex items-center space-x-1.5 transition-colors ${
              activeMenuTab === 'timing'
                ? 'font-bold text-[var(--text-main)] underline underline-offset-8 decoration-2 decoration-blue-600'
                : 'text-gray-500 hover:text-[var(--text-main)]'
            }`}
          >
            <Clock className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
            <span>Phase 4 Entry Timing</span>
          </button>
        </div>

        {/* View 1: Real Company Financial Statements & Fundamentals */}
        {activeMenuTab === 'financials' && (
          !fin ? (
            <div className="py-12 text-center text-gray-500 font-mono text-xs">
              No financial statements recorded in database for {stock.ticker}.
            </div>
          ) : (
            <div className="space-y-6">
              {/* Income & Cash Flow Grid */}
              <div className="space-y-3 font-mono text-xs">
                <div className="text-gray-400 uppercase tracking-wider text-[10px]">
                  Income Statement & Cash Flow (TTM)
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
                  <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                    <span className="text-gray-400 block text-[10px]">REVENUE</span>
                    <strong className="text-slate-900 dark:text-white text-lg block font-bold">
                      {formatCurrencyBillions(fin.revenue)}
                    </strong>
                    <span className="text-[10px] text-emerald-500 block">
                      YoY: {fin.revenue_growth_yoy ? `+${fin.revenue_growth_yoy.toFixed(1)}%` : '-'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                    <span className="text-gray-400 block text-[10px]">GROSS PROFIT</span>
                    <strong className="text-slate-900 dark:text-white text-lg block font-bold">
                      {formatCurrencyBillions(fin.gross_profit)}
                    </strong>
                    <span className="text-[10px] text-gray-500 block">
                      Margin: {fin.gross_margin ? `${fin.gross_margin.toFixed(1)}%` : '-'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                    <span className="text-gray-400 block text-[10px]">NET INCOME</span>
                    <strong className="text-slate-900 dark:text-white text-lg block font-bold">
                      {formatCurrencyBillions(fin.net_income)}
                    </strong>
                    <span className="text-[10px] text-gray-500 block">
                      EPS: {fin.eps ? `$${fin.eps.toFixed(2)}` : '-'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                    <span className="text-gray-400 block text-[10px]">EBITDA</span>
                    <strong className="text-slate-900 dark:text-white text-lg block font-bold">
                      {formatCurrencyBillions(fin.ebitda)}
                    </strong>
                    <span className="text-[10px] text-gray-500 block">
                      EV/EBITDA: {fin.ev_to_ebitda ? `${fin.ev_to_ebitda.toFixed(1)}x` : '-'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                    <span className="text-gray-400 block text-[10px]">FREE CASH FLOW</span>
                    <strong className="text-slate-900 dark:text-white text-lg block font-bold">
                      {formatCurrencyBillions(fin.free_cash_flow)}
                    </strong>
                    <span className="text-[10px] text-gray-500 block">
                      FCF Margin: {fin.fcf_margin ? `${fin.fcf_margin.toFixed(1)}%` : '-'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                    <span className="text-gray-400 block text-[10px]">CASH & EQUIVALENTS</span>
                    <strong className="text-slate-900 dark:text-white text-lg block font-bold">
                      {formatCurrencyBillions(fin.cash)}
                    </strong>
                    <span className="text-[10px] text-gray-500 block">
                      Total Debt: {formatCurrencyBillions(fin.total_debt)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Financial Ratios & Return Metrics */}
              <div className="space-y-3 font-mono text-xs pt-2">
                <div className="text-gray-400 uppercase tracking-wider text-[10px]">
                  Valuation Multiples & Efficiency Ratios
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
                  <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                    <span className="text-gray-400 block text-[10px]">P/E RATIO (TTM)</span>
                    <strong className="text-blue-600 dark:text-blue-400 text-lg block font-bold">
                      {fin.pe_ratio ? `${fin.pe_ratio.toFixed(1)}x` : '-'}
                    </strong>
                    <span className="text-[10px] text-gray-500 block">Trailing Multiples</span>
                  </div>

                  <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                    <span className="text-gray-400 block text-[10px]">FORWARD P/E</span>
                    <strong className="text-blue-600 dark:text-blue-400 text-lg block font-bold">
                      {fin.forward_pe ? `${fin.forward_pe.toFixed(1)}x` : '-'}
                    </strong>
                    <span className="text-[10px] text-gray-500 block">Next 12M Consensus</span>
                  </div>

                  <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                    <span className="text-gray-400 block text-[10px]">ROIC</span>
                    <strong className="text-emerald-500 text-lg block font-bold">
                      {fin.roic ? `${fin.roic.toFixed(1)}%` : '-'}
                    </strong>
                    <span className="text-[10px] text-gray-500 block">Return on Capital</span>
                  </div>

                  <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                    <span className="text-gray-400 block text-[10px]">ROE</span>
                    <strong className="text-emerald-500 text-lg block font-bold">
                      {fin.roe ? `${fin.roe.toFixed(1)}%` : '-'}
                    </strong>
                    <span className="text-[10px] text-gray-500 block">Return on Equity</span>
                  </div>

                  <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                    <span className="text-gray-400 block text-[10px]">OPERATING MARGIN</span>
                    <strong className="text-slate-900 dark:text-white text-lg block font-bold">
                      {fin.operating_margin ? `${fin.operating_margin.toFixed(1)}%` : '-'}
                    </strong>
                    <span className="text-[10px] text-gray-500 block">EBIT / Revenue</span>
                  </div>

                  <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                    <span className="text-gray-400 block text-[10px]">EPS SURPRISE</span>
                    <strong className="text-emerald-500 text-lg block font-bold">
                      {fin.eps_surprise_pct ? `+${fin.eps_surprise_pct.toFixed(1)}%` : '-'}
                    </strong>
                    <span className="text-[10px] text-gray-500 block">Latest Beat</span>
                  </div>
                </div>
              </div>
            </div>
          )
        )}

        {/* View 2: Multi-Factor Quantitative Subscores */}
        {activeMenuTab === 'scores' && (
          !sc ? (
            <div className="py-12 text-center text-gray-500 font-mono text-xs">
              No score records found in database for {stock.ticker}.
            </div>
          ) : (
            <section className="space-y-4 font-mono text-xs">
              <div className="text-gray-400 uppercase tracking-wider text-[10px]">
                Quantitative Factor Weights & Subscore Breakdown
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
                <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] text-center space-y-1">
                  <span className="text-gray-400 block text-[10px] uppercase">QUALITY (25%)</span>
                  <strong className="text-slate-900 dark:text-white text-xl block font-bold">
                    {sc.quality_score?.toFixed(1) || '-'}
                  </strong>
                  <span className="text-[10px] text-gray-500 font-sans block">ROIC & Margins</span>
                </div>

                <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] text-center space-y-1">
                  <span className="text-gray-400 block text-[10px] uppercase">GROWTH (20%)</span>
                  <strong className="text-slate-900 dark:text-white text-xl block font-bold">
                    {sc.growth_score?.toFixed(1) || '-'}
                  </strong>
                  <span className="text-[10px] text-gray-500 font-sans block">YoY Rev & EPS</span>
                </div>

                <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] text-center space-y-1">
                  <span className="text-gray-400 block text-[10px] uppercase">VALUATION (20%)</span>
                  <strong className="text-slate-900 dark:text-white text-xl block font-bold">
                    {sc.valuation_score?.toFixed(1) || '-'}
                  </strong>
                  <span className="text-[10px] text-gray-500 font-sans block">P/E & EV/EBITDA</span>
                </div>

                <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] text-center space-y-1">
                  <span className="text-gray-400 block text-[10px] uppercase">EARNINGS (15%)</span>
                  <strong className="text-slate-900 dark:text-white text-xl block font-bold">
                    {sc.earnings_score?.toFixed(1) || '-'}
                  </strong>
                  <span className="text-[10px] text-gray-500 font-sans block">Surprises & Revisions</span>
                </div>

                <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] text-center space-y-1">
                  <span className="text-gray-400 block text-[10px] uppercase">TECHNICAL (10%)</span>
                  <strong className="text-slate-900 dark:text-white text-xl block font-bold">
                    {sc.technical_score?.toFixed(1) || '-'}
                  </strong>
                  <span className="text-[10px] text-gray-500 font-sans block">Trend & SMAs</span>
                </div>

                <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] text-center space-y-1">
                  <span className="text-gray-400 block text-[10px] uppercase">REL. STRENGTH (10%)</span>
                  <strong className="text-slate-900 dark:text-white text-xl block font-bold">
                    {sc.relative_strength_score?.toFixed(1) || '-'}
                  </strong>
                  <span className="text-[10px] text-gray-500 font-sans block">Stock vs Sector</span>
                </div>
              </div>
            </section>
          )
        )}

        {/* View 3: Phase 4 Entry Timing Engine Panel */}
        {activeMenuTab === 'timing' && (
          !entryDetail ? (
            <div className="py-12 text-center text-gray-500 font-mono text-xs">
              No Phase 4 entry timing calculations recorded in database for {stock.ticker}.
            </div>
          ) : (
            <section className="space-y-4 font-mono text-xs">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-[var(--border-color)] pb-3">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider font-mono">
                    Phase 4 Entry Timing Engine
                  </h2>
                </div>

                <div className="flex items-center space-x-4">
                  <span className="text-gray-400">
                    Entry Score:{' '}
                    <strong className="text-blue-600 dark:text-blue-400 text-sm">
                      {entryDetail.entry_score.toFixed(1)} / 100
                    </strong>
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                    {entryDetail.status} ENTRY
                  </span>
                </div>
              </div>

              {/* Entry Range Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-1">
                <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                  <span className="text-[10px] text-gray-400 uppercase">PREFERRED ENTRY ZONE</span>
                  <div className="text-lg font-bold text-emerald-500 font-mono">
                    ${entryDetail.entry_zone.entry_zone_low.toFixed(2)} – ${entryDetail.entry_zone.entry_zone_high.toFixed(2)}
                  </div>
                  <span className="text-[10px] text-gray-500 block">
                    Current Market: ${entryDetail.entry_zone.current_price.toFixed(2)}
                  </span>
                </div>

                <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                  <span className="text-[10px] text-gray-400 uppercase">INVALIDATION LEVEL (STOP)</span>
                  <div className="text-lg font-bold text-rose-500 font-mono">
                    ${entryDetail.entry_zone.invalidation_price.toFixed(2)}
                  </div>
                  <span className="text-[10px] text-gray-500 block">
                    Target Price: ${entryDetail.entry_zone.target_price.toFixed(2)}
                  </span>
                </div>

                <div className="p-3.5 rounded border border-[var(--border-color)] bg-[var(--bg-main)] space-y-1">
                  <span className="text-[10px] text-gray-400 uppercase">RISK / REWARD RATIO</span>
                  <div className="text-lg font-bold text-amber-500 font-mono">
                    {entryDetail.entry_zone.risk_reward_ratio.toFixed(2)} R/R
                  </div>
                  <span className="text-[10px] text-gray-500 block">
                    Event Risk Level: {entryDetail.event_risk}
                  </span>
                </div>
              </div>

              {/* Setups */}
              {entryDetail.setups && entryDetail.setups.length > 0 && (
                <div className="space-y-2 pt-2">
                  <span className="text-gray-400 uppercase tracking-wider text-[10px]">
                    Detected Technical Signals & Patterns
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {entryDetail.setups.map((s, i) => (
                      <div
                        key={i}
                        className="flex items-center space-x-1.5 px-3 py-1 rounded bg-[var(--bg-main)] border border-[var(--border-color)] text-xs text-slate-800 dark:text-gray-200"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                        <strong className="font-mono">{s.setup_type}:</strong>
                        <span className="font-sans font-light">{s.description}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </section>
          )
        )}
      </main>
    </div>
  );
}
