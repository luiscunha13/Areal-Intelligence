'use client';

import React from 'react';

interface DimensionsProps {
  growth: number;
  inflation: number;
  rates: number;
  liquidity: number;
  credit: number;
  risk: number;
}

export const DimensionGauges: React.FC<DimensionsProps> = ({
  growth,
  inflation,
  rates,
  liquidity,
  credit,
  risk,
}) => {
  const dimensions = [
    { name: 'Growth', score: growth, desc: 'GDP, IP, Retail Sales, Unemployment' },
    { name: 'Inflation', score: inflation, desc: 'CPI, Core CPI, Core PCE' },
    { name: 'Rates', score: rates, desc: 'Yield Curve 10Y-2Y, Real Yields' },
    { name: 'Liquidity', score: liquidity, desc: 'M2 Money Supply, Fed Total Assets' },
    { name: 'Credit', score: credit, desc: 'High Yield Option-Adjusted Spread' },
    { name: 'Risk', score: risk, desc: 'CBOE VIX Volatility Index' },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {dimensions.map((d) => (
        <div key={d.name} className="card-panel card-panel-hover rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-semibold text-slate-800 dark:text-gray-200 uppercase tracking-wider">{d.name}</h3>
              <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">{d.desc}</p>
            </div>
            <div className="text-lg font-mono font-bold text-slate-900 dark:text-white">
              {d.score}
            </div>
          </div>

          <div className="mt-3">
            <div className="h-1.5 w-full bg-slate-200 dark:bg-[#1E2330] rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600 dark:bg-blue-500 rounded-full"
                style={{ width: `${Math.max(4, Math.min(100, d.score))}%` }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
