'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Navbar } from '@/components/Navbar';
import { Target, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react';

interface CandidateItem {
  id: number;
  company_id: number;
  date: string;
  candidate_score: number;
  stock_score: number;
  sector_score: number;
  category: string;
  confidence: string;
  risk_flags?: string[];
  explanations?: string[];
  company: {
    ticker: string;
    company_name: string;
    exchange: string;
  };
}

const FALLBACK_CANDIDATES: CandidateItem[] = [
  {
    id: 1,
    company_id: 1,
    date: '2026-08-14',
    candidate_score: 91.9,
    stock_score: 92.5,
    sector_score: 91.0,
    category: 'Strong Candidate',
    confidence: 'High',
    risk_flags: ['HIGH_VALUATION'],
    explanations: [
      "Sector 'Information Technology' is currently in a top-performing leadership regime (91.0/100).",
      'Strong quality metrics (Score: 94.2) backed by high ROIC and profit margins.',
      'Robust revenue and EPS growth momentum (Score: 97.8).',
      'Favorable price trend and momentum above key moving averages.'
    ],
    company: { ticker: 'NVDA', company_name: 'NVIDIA Corporation', exchange: 'NASDAQ' }
  },
  {
    id: 2,
    company_id: 2,
    date: '2026-08-14',
    candidate_score: 90.3,
    stock_score: 89.8,
    sector_score: 91.0,
    category: 'Strong Candidate',
    confidence: 'High',
    risk_flags: [],
    explanations: [
      "Sector 'Information Technology' is currently in a top-performing leadership regime (91.0/100).",
      'Exceptional balance-sheet quality (Quality Score: 96.0).',
      'Consistent earnings surprises and positive analyst revision momentum.'
    ],
    company: { ticker: 'MSFT', company_name: 'Microsoft Corporation', exchange: 'NASDAQ' }
  },
  {
    id: 3,
    company_id: 6,
    date: '2026-08-14',
    candidate_score: 87.9,
    stock_score: 83.9,
    sector_score: 94.0,
    category: 'Strong Candidate',
    confidence: 'High',
    risk_flags: ['HIGH_VALUATION'],
    explanations: [
      "Sector 'Health Care' exhibits strong defensive expansion momentum (94.0/100).",
      'High growth score (93.5) driven by drug pipeline expansion.',
      'Strong price relative strength vs benchmark S&P 500.'
    ],
    company: { ticker: 'LLY', company_name: 'Eli Lilly and Company', exchange: 'NYSE' }
  },
  {
    id: 4,
    company_id: 8,
    date: '2026-08-14',
    candidate_score: 82.5,
    stock_score: 81.2,
    sector_score: 84.5,
    category: 'Strong Candidate',
    confidence: 'High',
    risk_flags: [],
    explanations: [
      "Sector 'Financials' benefits from favorable net interest income trends (84.5/100).",
      'Attractive valuation score (82.0) relative to market peers.',
      'Solid ROE and capital return trajectory.'
    ],
    company: { ticker: 'JPM', company_name: 'JPMorgan Chase & Co.', exchange: 'NYSE' }
  }
];

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<CandidateItem[]>(FALLBACK_CANDIDATES);
  const [loading, setLoading] = useState(true);

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/stocks/screener?min_score=50&limit=50');
      if (res.ok) {
        const raw = await res.json();
        const list = Array.isArray(raw) ? raw : (raw.candidates || []);
        if (list.length > 0) {
          setCandidates(list.map((s: any, idx: number) => ({
            id: idx + 1,
            company_id: idx + 1,
            date: s.date || new Date().toISOString().split('T')[0],
            candidate_score: Math.round((s.composite_score || 50) * 10) / 10,
            stock_score: Math.round((s.quality_score || s.composite_score || 50) * 10) / 10,
            sector_score: Math.round((s.momentum_score || 85) * 10) / 10,
            category: (s.composite_score || 50) >= 65 ? 'Strong Candidate' : 'Candidate',
            confidence: 'High',
            risk_flags: [],
            explanations: [
              `Sector '${s.sector || 'General'}' exhibits strong leadership momentum.`,
              `Composite score of ${Math.round(s.composite_score || 50)}/100 across momentum and trend factors.`
            ],
            company: { ticker: s.ticker, company_name: s.name || s.ticker, exchange: 'US' }
          })));
        }
      }
    } catch (err) {
      console.warn('Backend API unavailable, using local candidates state.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, []);

  return (
    <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-main)] transition-colors">
      <Navbar />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[var(--border-color)] pb-6">
          <div>
            <div className="flex items-center space-x-2 text-xs font-mono text-amber-600 dark:text-amber-400 mb-1">
              <Target className="h-3.5 w-3.5" />
              <span>SUBPHASE 3.8 OPPORTUNITY ENGINE</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight font-sans">Systematic Investment Candidates</h1>
            <p className="text-xs text-gray-500 mt-1 max-w-2xl">
              Integrates Macro Regime (Phase 1) + Sector Leadership (Phase 2) + Multi-Factor Stock Score (Phase 3) into ranked candidate opportunities.
            </p>
          </div>

          <button
            onClick={fetchCandidates}
            disabled={loading}
            className="flex items-center space-x-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-card)] px-3 py-1.5 text-xs font-mono text-[var(--text-main)] hover:border-gray-400 transition-all shadow-sm shrink-0 self-start sm:self-auto"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Candidate Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {candidates.map(item => (
            <div key={item.id} className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] p-6 shadow-sm flex flex-col justify-between space-y-4 hover:border-amber-500/40 transition-colors">
              
              <div>
                {/* Top Bar */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <Link href={`/stocks/${item.company.ticker}`} className="text-xl font-bold font-mono text-amber-500 hover:underline">
                        {item.company.ticker}
                      </Link>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wide uppercase ${
                        item.category === 'Strong Candidate' ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20' :
                        item.category === 'Candidate' ? 'bg-blue-500/10 text-blue-600 border border-blue-500/20' :
                        'bg-gray-500/10 text-gray-500 border border-gray-500/20'
                      }`}>
                        {item.category}
                      </span>
                    </div>
                    <h2 className="text-sm font-sans font-medium text-[var(--text-main)] mt-0.5">
                      <Link href={`/stocks/${item.company.ticker}`} className="hover:underline">
                        {item.company.company_name}
                      </Link>
                    </h2>
                  </div>

                  {/* Candidate Score Circle */}
                  <div className="text-right">
                    <span className="text-2xl font-extrabold font-mono text-[var(--text-main)]">
                      {item.candidate_score.toFixed(1)}
                    </span>
                    <span className="block text-[10px] text-gray-400 font-mono uppercase">Candidate Score</span>
                  </div>
                </div>

                {/* Subscores Bar */}
                <div className="grid grid-cols-2 gap-2 mt-4 text-xs font-mono bg-gray-50 dark:bg-slate-900/50 p-2.5 rounded border border-[var(--border-color)]">
                  <div>
                    <span className="text-gray-400">Stock Score:</span> <strong className="text-purple-400">{item.stock_score.toFixed(1)}</strong>
                  </div>
                  <div>
                    <span className="text-gray-400">Sector Score:</span> <strong className="text-emerald-400">{item.sector_score.toFixed(1)}</strong>
                  </div>
                </div>

                {/* Thesis Bullets */}
                {item.explanations && item.explanations.length > 0 && (
                  <div className="mt-4 space-y-1.5">
                    <span className="text-[11px] font-semibold text-gray-500 uppercase font-mono tracking-wider">Deterministic Thesis</span>
                    <ul className="space-y-1 text-xs text-[var(--text-main)]">
                      {item.explanations.map((exp, idx) => (
                        <li key={idx} className="flex items-start space-x-1.5">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
                          <span>{exp}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Risk Flags */}
                {item.risk_flags && item.risk_flags.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {item.risk_flags.map((flag, idx) => (
                      <span key={idx} className="flex items-center space-x-1 bg-amber-500/10 text-amber-600 dark:text-amber-400 text-[10px] font-mono px-2 py-0.5 rounded border border-amber-500/20">
                        <AlertTriangle className="h-3 w-3" />
                        <span>{flag}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-[var(--border-color)] text-[10px] font-mono text-gray-400 flex items-center justify-between">
                <span>Confidence: <strong className="text-[var(--text-main)]">{item.confidence}</strong></span>
                <span>Evaluated: {item.date}</span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
