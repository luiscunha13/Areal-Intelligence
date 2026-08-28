'use client';

import React from 'react';

interface IndicatorProps {
  title: string;
  value: string;
  unit: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  category: string;
}

export const IndicatorCard: React.FC<IndicatorProps> = ({
  title,
  value,
  unit,
  change,
  trend,
  category,
}) => {
  return (
    <div className="card-panel card-panel-hover rounded-lg p-4">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono uppercase tracking-wider text-gray-500 dark:text-gray-400">
          {category}
        </span>
        <span className={`text-[11px] font-mono font-medium ${
          trend === 'up' ? 'text-emerald-600 dark:text-emerald-400' : trend === 'down' ? 'text-rose-600 dark:text-rose-400' : 'text-gray-500 dark:text-gray-400'
        }`}>
          {change}
        </span>
      </div>

      <div className="mt-2">
        <h4 className="text-xs font-medium text-slate-700 dark:text-gray-300">{title}</h4>
        <div className="mt-1 flex items-baseline gap-1">
          <span className="text-xl font-bold font-mono text-slate-900 dark:text-white tracking-tight">{value}</span>
          <span className="text-[11px] text-gray-500 dark:text-gray-400">{unit}</span>
        </div>
      </div>
    </div>
  );
};
