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

interface ChartProps {
  featuresHistory: any[];
}

export const HistoricalCharts: React.FC<ChartProps> = ({ featuresHistory }) => {
  const [activeTab, setActiveTab] = useState<'overall' | 'dimensions'>('overall');

  const formattedData = featuresHistory.map((item) => ({
    date: item.feature_date || item.date,
    Overall: Math.round(item.overall_score || 50),
    Growth: Math.round(item.growth_score || item.dimensions?.growth || 50),
    Inflation: Math.round(item.inflation_score || item.dimensions?.inflation || 50),
    Rates: Math.round(item.rates_score || item.dimensions?.rates || 50),
    Liquidity: Math.round(item.liquidity_score || item.dimensions?.liquidity || 50),
    Credit: Math.round(item.credit_score || item.dimensions?.credit || 50),
    Risk: Math.round(item.risk_score || item.dimensions?.risk || 50),
  }));

  return (
    <div className="card-panel rounded-lg p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white uppercase tracking-wider">Historical Score Trajectory</h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Point-in-time time-series quantitative score evolution</p>
        </div>

        <div className="flex rounded bg-slate-100 dark:bg-[#090B0E] p-1 border border-[var(--border-color)]">
          <button
            onClick={() => setActiveTab('overall')}
            className={`rounded px-3 py-1 text-xs font-mono transition-all ${
              activeTab === 'overall'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Overall
          </button>
          <button
            onClick={() => setActiveTab('dimensions')}
            className={`rounded px-3 py-1 text-xs font-mono transition-all ${
              activeTab === 'dimensions'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Dimensions
          </button>
        </div>
      </div>

      <div className="h-64 sm:h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          {activeTab === 'overall' ? (
            <AreaChart data={formattedData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
              <XAxis dataKey="date" stroke="#94A3B8" tick={{ fontSize: 11, fill: '#64748B' }} />
              <YAxis domain={[0, 100]} stroke="#94A3B8" tick={{ fontSize: 11, fill: '#64748B' }} />
              <Tooltip
                contentStyle={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)', borderRadius: '4px' }}
                itemStyle={{ color: 'var(--text-main)', fontSize: '12px', fontFamily: 'monospace' }}
              />
              <Area type="monotone" dataKey="Overall" stroke="#3B82F6" strokeWidth={2} fillOpacity={0.15} fill="#3B82F6" />
            </AreaChart>
          ) : (
            <LineChart data={formattedData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
              <XAxis dataKey="date" stroke="#94A3B8" tick={{ fontSize: 11, fill: '#64748B' }} />
              <YAxis domain={[0, 100]} stroke="#94A3B8" tick={{ fontSize: 11, fill: '#64748B' }} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)', borderRadius: '4px' }} />
              <Line type="monotone" dataKey="Growth" stroke="#3B82F6" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="Inflation" stroke="#F59E0B" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="Rates" stroke="#8B5CF6" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="Liquidity" stroke="#10B981" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="Credit" stroke="#06B6D4" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="Risk" stroke="#F43F5E" strokeWidth={1.5} dot={false} />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};
