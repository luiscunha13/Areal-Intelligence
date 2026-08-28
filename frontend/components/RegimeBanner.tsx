'use client';

import React from 'react';

interface RegimeBannerProps {
  regime: string;
  overallScore: number;
  confidence: number;
  asofDate: string;
}

export const RegimeBanner: React.FC<RegimeBannerProps> = ({
  regime,
  overallScore,
  confidence,
  asofDate,
}) => {
  return (
    <div className="card-panel rounded-lg p-6 sm:p-7">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="inline-block rounded bg-blue-500/10 dark:bg-blue-500/20 px-2 py-0.5 text-[11px] font-mono font-medium text-blue-600 dark:text-blue-400 border border-blue-500/20">
              CURRENT REGIME
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">As of {asofDate}</span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-slate-900 dark:text-white">
            {regime}
          </h2>

          <p className="text-xs text-gray-600 dark:text-gray-400 max-w-xl leading-relaxed">
            Multi-indicator composite synthesis across Growth, Inflation, Rates, Liquidity, Credit Spreads, and Volatility.
          </p>
        </div>

        <div className="flex items-center gap-8 self-start md:self-auto border-t md:border-t-0 md:border-l border-[var(--border-color)] pt-4 md:pt-0 md:pl-8">
          <div>
            <div className="text-[11px] font-mono text-gray-500 dark:text-gray-400 uppercase tracking-wider">Overall Score</div>
            <div className="mt-1 text-3xl font-semibold text-slate-900 dark:text-white font-mono flex items-baseline gap-1">
              {overallScore}
              <span className="text-xs font-normal text-gray-500">/100</span>
            </div>
          </div>

          <div>
            <div className="text-[11px] font-mono text-gray-500 dark:text-gray-400 uppercase tracking-wider">Signal Strength</div>
            <div className="mt-1 text-3xl font-semibold text-slate-700 dark:text-gray-300 font-mono">
              {confidence}%
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
