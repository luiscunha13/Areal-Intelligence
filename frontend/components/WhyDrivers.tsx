'use client';

import React from 'react';

interface WhyDriversProps {
  positive: string[];
  negative: string[];
}

export const WhyDrivers: React.FC<WhyDriversProps> = ({ positive, negative }) => {
  return (
    <div className="card-panel rounded-lg p-6">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white uppercase tracking-wider">Regime Drivers & Catalysts</h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Factor decomposition behind current market regime classification</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Positive Drivers */}
        <div className="card-subtle rounded p-4">
          <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-3">
            Positive Support Factors
          </div>
          <ul className="space-y-2">
            {positive.map((item, idx) => (
              <li key={idx} className="flex items-start space-x-2 text-xs text-slate-700 dark:text-gray-300">
                <span className="text-emerald-500 font-bold">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Negative Drivers */}
        <div className="card-subtle rounded p-4">
          <div className="text-xs font-semibold text-rose-600 dark:text-rose-400 uppercase tracking-wider mb-3">
            Headwinds & Risks
          </div>
          <ul className="space-y-2">
            {negative.map((item, idx) => (
              <li key={idx} className="flex items-start space-x-2 text-slate-700 dark:text-gray-300">
                <span className="text-rose-500 font-bold">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
