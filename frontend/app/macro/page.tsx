'use client';

import React, { useEffect, useState } from 'react';
import { Navbar } from '../../components/Navbar';
import { IndicatorSplitView } from '../../components/IndicatorSplitView';
import { ScoresOverview } from '../../components/ScoresOverview';

export default function MacroPage() {
  const [activeTab, setActiveTab] = useState<'indicators' | 'overview'>('overview');
  const [currentRegime, setCurrentRegime] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [regimeRes, historyRes] = await Promise.all([
        fetch('/api/macro/regime/current'),
        fetch('/api/macro/regime?limit=60'),
      ]);

      if (regimeRes.ok) {
        const regimeData = await regimeRes.json();
        setCurrentRegime(regimeData);
      }
      if (historyRes.ok) {
        const historyData = await historyRes.json();
        setHistory(historyData);
      }
    } catch (err) {
      console.warn('Using fallback regime data');
      setCurrentRegime({
        date: new Date().toISOString().split('T')[0],
        regime: 'Neutral / Transition',
        overall_score: 55.5,
        confidence: 92.7,
        dimensions: { growth: 40.3, inflation: 79.6, rates: 20.8, liquidity: 36.7, credit: 91.1, risk: 70.7 },
        why: {
          positive: ['Credit spreads tightening & financing conditions easy', 'Market volatility low'],
          negative: ['Economic growth momentum slowing down', 'Liquidity contracting'],
        },
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  return (
    <div className="h-screen overflow-hidden flex flex-col bg-[var(--bg-main)] text-[var(--text-main)] transition-colors">
      <Navbar />

      <main className="flex-1 overflow-hidden flex flex-col w-full">
        {/* Sub-Header & Navigation — always visible */}
        <div className="shrink-0 flex items-center justify-between border-b border-[var(--border-color)] px-4 sm:px-6 py-3 bg-[var(--bg-main)] z-10">
          <div className="flex items-center space-x-6">
            <button
              onClick={() => setActiveTab('overview')}
              className={`text-sm transition-colors ${
                activeTab === 'overview'
                  ? 'font-bold text-[var(--text-main)] underline underline-offset-8 decoration-2 decoration-blue-600'
                  : 'font-normal text-gray-500 hover:text-[var(--text-main)]'
              }`}
            >
              Scores &amp; Overview
            </button>
            <button
              onClick={() => setActiveTab('indicators')}
              className={`text-sm transition-colors ${
                activeTab === 'indicators'
                  ? 'font-bold text-[var(--text-main)] underline underline-offset-8 decoration-2 decoration-blue-600'
                  : 'font-normal text-gray-500 hover:text-[var(--text-main)]'
              }`}
            >
              Indicator Explorer
            </button>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={fetchData}
              disabled={loading}
              className="text-xs font-mono text-gray-500 hover:text-[var(--text-main)] transition-colors"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Tab: Scores & Overview */}
        {activeTab === 'overview' && (
          <section className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 pb-10">
            <ScoresOverview currentRegime={currentRegime} history={history} loading={loading} />
          </section>
        )}

        {/* Tab: Indicator Explorer */}
        {activeTab === 'indicators' && (
          <section className="flex-1 overflow-hidden px-4 sm:px-6 py-4">
            <IndicatorSplitView />
          </section>
        )}
      </main>
    </div>
  );
}
