'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Brush,
  ReferenceArea,
  ReferenceLine,
} from 'recharts';
import { Search, ChevronDown } from 'lucide-react';

export interface IndicatorItem {
  id: string;
  fred_series_id: string;
  name: string;
  category: string;
  description?: string;
  frequency?: string;
  unit?: string;
  analysis_overview?: string;
  impact_rising?: string;
  impact_falling?: string;
}

const CATEGORIES = [
  { id: 'all', label: 'All' },
  { id: 'growth', label: 'Growth' },
  { id: 'inflation', label: 'Inflation' },
  { id: 'rates', label: 'Rates' },
  { id: 'liquidity', label: 'Liquidity' },
  { id: 'credit', label: 'Credit' },
  { id: 'risk', label: 'Risk' },
  { id: 'benchmark', label: 'Benchmark' },
];

const COMPARISON_COLOR = '#64748B'; // Slate Gray - neutral, balanced color for comparison benchmarks

const BENCHMARKS = [
  { id: 'none', label: 'None' },
  { id: 'SP500', label: 'S&P 500' },
  { id: 'IQ12260', label: 'Gold' },
  { id: 'NASDAQCOM', label: 'Nasdaq' },
  { id: 'DTWEXBGS', label: 'USD Index' },
  { id: 'DGS10', label: '10Y Yield' },
  { id: 'VIXCLS', label: 'VIX' },
];

const TRIGGER_THRESHOLDS: Record<string, { y: number; label: string; color: string }[]> = {
  SAHMREALTIME: [{ y: 0.5, label: 'Sahm Rule Threshold (0.5%)', color: '#EF4444' }],
  T10Y2Y: [{ y: 0.0, label: 'Inversion (0.0)', color: '#EF4444' }],
  VIXCLS: [
    { y: 20.0, label: 'Elevated Vol (20)', color: '#F59E0B' },
    { y: 30.0, label: 'Acute Stress (30)', color: '#EF4444' },
  ],
  NFCI: [{ y: 0.0, label: 'Tightening Border (0.0)', color: '#64748B' }],
  STLFSI4: [{ y: 0.0, label: 'Stress Border (0.0)', color: '#64748B' }],
};

const CustomTooltip = ({ active, payload, label, activeItem, activeBenchmark, isRebased, isYoY }: any) => {
  if (!active || !payload || !payload.length) return null;

  const primaryData = payload.find((p: any) => p.dataKey === 'value');
  const compareData = payload.find((p: any) => p.dataKey === 'compareValue');

  return (
    <div className="bg-[var(--bg-main)] border border-[var(--border-color)] p-2.5 rounded shadow-lg text-xs font-mono space-y-1.5 z-50 min-w-[200px]">
      <div className="text-gray-400 font-bold border-b border-[var(--border-color)] pb-1 flex items-center justify-between">
        <span>{label}</span>
      </div>

      {primaryData && (
        <div className="flex items-center justify-between gap-4">
          <span className="text-blue-600 dark:text-blue-400 flex items-center gap-1.5 font-sans text-[11px] font-medium truncate max-w-[120px]">
            <span className="w-2 h-2 rounded-full bg-blue-600 shrink-0"></span>
            {activeItem?.name || 'Indicator'}
          </span>
          <span className="font-bold text-[var(--text-main)]">
            {isRebased || isYoY
              ? `${primaryData.value >= 0 ? '+' : ''}${primaryData.value}%`
              : `${primaryData.value} ${activeItem?.unit === 'percent' || activeItem?.unit === 'index' ? '%' : ''}`}
          </span>
        </div>
      )}

      {compareData && compareData.value !== null && compareData.value !== undefined && (
        <div className="flex items-center justify-between gap-4 pt-0.5">
          <span className="flex items-center gap-1.5 font-sans text-[11px] font-medium truncate max-w-[120px]" style={{ color: COMPARISON_COLOR }}>
            <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: COMPARISON_COLOR }}></span>
            {activeBenchmark?.label || 'Benchmark'}
          </span>
          <span className="font-bold text-[var(--text-main)]">
            {isRebased || isYoY
              ? `${compareData.value >= 0 ? '+' : ''}${compareData.value}%`
              : `${compareData.value}`}
          </span>
        </div>
      )}
    </div>
  );
};

export const IndicatorSplitView: React.FC = () => {
  const [seriesList, setSeriesList] = useState<IndicatorItem[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedId, setSelectedId] = useState<string>('CPIAUCSL');
  const [timeframe, setTimeframe] = useState<string>('5Y');
  
  const [activeSeriesMeta, setActiveSeriesMeta] = useState<any>(null);
  const [observations, setObservations] = useState<{ date: string; value: number }[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Benchmark Comparison & Transformation States ('nominal' | 'rebased' | 'yoy')
  const [compareId, setCompareId] = useState<string>('none');
  const [compareObservations, setCompareObservations] = useState<{ date: string; value: number }[]>([]);
  const [loadingCompare, setLoadingCompare] = useState<boolean>(false);
  const [transformMode, setTransformMode] = useState<'nominal' | 'rebased' | 'yoy'>('nominal');

  const isRebased = transformMode === 'rebased';
  const isYoY = transformMode === 'yoy';

  // Recession & Cross-Asset Heatmap States
  const [recessionObservations, setRecessionObservations] = useState<{ date: string; value: number }[]>([]);
  const [heatmapData, setHeatmapData] = useState<Record<string, { date: string; value: number }[]>>({});

  // Custom Comparison Combobox States & Click Outside
  const [compareSearchQuery, setCompareSearchQuery] = useState<string>('');
  const [isCompareOpen, setIsCompareOpen] = useState<boolean>(false);
  const compareDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (compareDropdownRef.current && !compareDropdownRef.current.contains(event.target as Node)) {
        setIsCompareOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const activeCustomSeries = useMemo(() => {
    return seriesList.find((s) => s.fred_series_id === compareId);
  }, [seriesList, compareId]);

  const isCustomActive = compareId !== 'none' && !BENCHMARKS.some((b) => b.id === compareId);

  const filteredCustomSeries = useMemo(() => {
    return seriesList.filter((s) => {
      if (s.fred_series_id === selectedId) return false;
      if (!compareSearchQuery.trim()) return true;
      const q = compareSearchQuery.toLowerCase();
      return s.name.toLowerCase().includes(q) || s.fred_series_id.toLowerCase().includes(q);
    });
  }, [seriesList, selectedId, compareSearchQuery]);

  // Box Selection Zoom States
  const [refAreaLeft, setRefAreaLeft] = useState<string>('');
  const [refAreaRight, setRefAreaRight] = useState<string>('');
  const [zoomedRange, setZoomedRange] = useState<{ left: string; right: string } | null>(null);

  // Reset box zoom when indicator or timeframe changes
  const handleSelectId = (id: string) => {
    setSelectedId(id);
    setZoomedRange(null);
  };

  const handleSelectTimeframe = (tf: string) => {
    setTimeframe(tf);
    setZoomedRange(null);
  };

  // 1. Fetch available Macro Series catalog directly from Backend Database
  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/macro/series');
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setSeriesList(data);
            if (!data.some((s: any) => s.fred_series_id === selectedId)) {
              setSelectedId(data[0].fred_series_id);
            }
          }
        }
      } catch (err) {
        console.error('Failed to fetch macro series catalog:', err);
      }
    };
    fetchCatalog();
  }, []);

  // 2. Fetch USREC NBER Recession Data
  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/macro/series/USREC?limit=50000')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.observations) {
          setRecessionObservations(
            data.observations.map((o: any) => ({
              date: o.date.split('T')[0],
              value: Number(o.value),
            }))
          );
        }
      })
      .catch((err) => console.error('Failed to fetch USREC recession data:', err));
  }, []);

  // 3. Fetch Cross-Asset Heatmap Benchmark Datasets
  useEffect(() => {
    const heatmapBenchmarks = ['SP500', 'IQ12260', 'DGS10', 'DTWEXBGS', 'VIXCLS'];
    heatmapBenchmarks.forEach((bmId) => {
      fetch(`http://127.0.0.1:8000/api/macro/series/${bmId}?limit=5000`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data && data.observations) {
            setHeatmapData((prev) => ({
              ...prev,
              [bmId]: data.observations.map((o: any) => ({
                date: o.date.split('T')[0],
                value: Number(o.value),
              })),
            }));
          }
        })
        .catch((err) => console.error(`Failed to fetch heatmap benchmark ${bmId}:`, err));
    });
  }, []);

  // 4. Fetch Real Series Observations directly from Backend Database
  useEffect(() => {
    let isMounted = true;
    const fetchSeriesData = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/macro/series/${selectedId}?limit=50000`);
        if (res.ok) {
          const data = await res.json();
          if (isMounted) {
            setActiveSeriesMeta(data);
            if (data.observations) {
              setObservations(
                data.observations
                  .filter((o: any) => o.value !== null && o.value !== undefined && !isNaN(o.value))
                  .map((o: any) => ({
                    date: o.date.split('T')[0],
                    value: Number(o.value),
                  }))
              );
            }
          }
        }
      } catch (err) {
        console.error('Failed to fetch series observations:', err);
        if (isMounted) setObservations([]);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchSeriesData();
    return () => {
      isMounted = false;
    };
  }, [selectedId]);

  // 5. Fetch Benchmark Comparison Series Observations
  useEffect(() => {
    if (compareId === 'none') {
      setCompareObservations([]);
      return;
    }
    let isMounted = true;
    setLoadingCompare(true);
    fetch(`http://127.0.0.1:8000/api/macro/series/${compareId}?limit=50000`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (isMounted && data && data.observations) {
          setCompareObservations(
            data.observations
              .filter((o: any) => o.value !== null && o.value !== undefined && !isNaN(o.value))
              .map((o: any) => ({
                date: o.date.split('T')[0],
                value: Number(o.value),
              }))
          );
        }
      })
      .catch((err) => console.error('Failed to fetch compare observations:', err))
      .finally(() => {
        if (isMounted) setLoadingCompare(false);
      });
    return () => {
      isMounted = false;
    };
  }, [compareId]);

  const filteredIndicators = seriesList.filter((item) => {
    const q = searchQuery.trim().toLowerCase();
    const cat = (item.category || '').toLowerCase();
    
    // When typing a search query, search globally across all categories
    const matchesCategory = !q ? (selectedCategory === 'all' || cat === selectedCategory) : true;
    const matchesSearch = !q || 
      (item.name || '').toLowerCase().includes(q) ||
      (item.fred_series_id || '').toLowerCase().includes(q) ||
      (item.description || '').toLowerCase().includes(q) ||
      cat.includes(q);

    return matchesCategory && matchesSearch;
  });

  const activeItem = seriesList.find((item) => item.fred_series_id === selectedId) || {
    id: selectedId,
    fred_series_id: selectedId,
    name: activeSeriesMeta?.name || selectedId,
    category: activeSeriesMeta?.category || 'macro',
    description: activeSeriesMeta?.description || '',
    frequency: activeSeriesMeta?.frequency || '',
    unit: activeSeriesMeta?.unit || '',
  };

  const activeBenchmark = useMemo(() => {
    const predefined = BENCHMARKS.find((b) => b.id === compareId);
    if (predefined) return predefined;
    const customSeries = seriesList.find((s) => s.fred_series_id === compareId);
    if (customSeries) {
      return { id: customSeries.fred_series_id, label: customSeries.name };
    }
    return { id: compareId, label: compareId };
  }, [compareId, seriesList]);

  // Derive values directly from database observations
  const latestObs = observations.length > 0 ? observations[observations.length - 1] : null;

  const displayValue = latestObs !== null && latestObs !== undefined
    ? `${latestObs.value}${activeItem.unit === 'percent' || activeItem.unit === 'index' ? '%' : ''}`
    : 'N/A';

  // 1. Percentile Rank Badge Calculation
  const percentileRank = useMemo(() => {
    if (!observations || observations.length === 0) return null;
    const sorted = [...observations].map((o) => o.value).sort((a, b) => a - b);
    const latestVal = observations[observations.length - 1]?.value;
    if (latestVal === undefined || latestVal === null) return null;
    const count = sorted.filter((v) => v <= latestVal).length;
    return Math.round((count / sorted.length) * 100);
  }, [observations]);

  // 6. Release & Staleness Badge Calculation
  const stalenessText = useMemo(() => {
    if (!latestObs?.date) return '';
    const obsDate = new Date(latestObs.date);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - obsDate.getTime()) / (1000 * 3600 * 24));
    const freq = activeSeriesMeta?.frequency || activeItem?.frequency || '';
    const formattedFreq = freq ? freq.charAt(0).toUpperCase() + freq.slice(1) : 'Macro';
    return `${formattedFreq} • Updated ${diffDays <= 0 ? 'today' : `${diffDays}d ago`}`;
  }, [latestObs, activeSeriesMeta, activeItem]);

  // 2. Compute NBER Recession Spans
  const recessionSpans = useMemo(() => {
    if (!recessionObservations || recessionObservations.length === 0) return [];
    const spans: { start: string; end: string }[] = [];
    let currentStart: string | null = null;
    let prevDate = '';

    for (const obs of recessionObservations) {
      if (obs.value === 1) {
        if (!currentStart) currentStart = obs.date;
      } else {
        if (currentStart) {
          spans.push({ start: currentStart, end: prevDate || obs.date });
          currentStart = null;
        }
      }
      prevDate = obs.date;
    }
    if (currentStart) {
      spans.push({ start: currentStart, end: prevDate });
    }
    return spans;
  }, [recessionObservations]);

  const filterHistoryByTimeframe = (data: { date: string; value: number }[], tf: string) => {
    if (!data || data.length === 0) return [];
    if (tf === 'ALL') return data;

    const lastPoint = data[data.length - 1];
    const lastYear = parseInt(lastPoint.date.split('-')[0]) || 2026;

    let startYear = 2010;
    if (tf === '1Y') startYear = lastYear - 1;
    else if (tf === 'YTD') return data.filter((d) => d.date.startsWith(`${lastYear}`));
    else if (tf === '3Y') startYear = lastYear - 3;
    else if (tf === '5Y') startYear = lastYear - 5;
    else if (tf === '10Y') startYear = lastYear - 10;

    return data.filter((d) => {
      const yr = parseInt(d.date.split('-')[0]);
      return yr >= startYear;
    });
  };

  const rawTimeframeData = filterHistoryByTimeframe(observations, timeframe);

  // 4. YoY Transformation logic if enabled
  const baseChartData = useMemo(() => {
    if (!rawTimeframeData || rawTimeframeData.length === 0) return [];
    if (!isYoY) return rawTimeframeData;

    const isDaily = rawTimeframeData.length > 500;
    const offset = isDaily ? 252 : 12;
    const isRateOrPercent =
      (activeItem.unit || '').toLowerCase().includes('percent') ||
      (activeItem.unit || '').toLowerCase().includes('yield') ||
      (activeItem.unit || '').toLowerCase().includes('rate');

    return rawTimeframeData.map((d, idx) => {
      if (idx < offset) return d;
      const prev = rawTimeframeData[idx - offset]?.value;
      if (prev === undefined || prev === null || prev === 0) return d;
      const yoyVal = isRateOrPercent
        ? d.value - prev
        : ((d.value - prev) / Math.abs(prev)) * 100;
      return {
        date: d.date,
        value: Number(yoyVal.toFixed(2)),
      };
    });
  }, [rawTimeframeData, isYoY, activeItem.unit]);

  const displayChartData = useMemo(() => {
    if (!zoomedRange || baseChartData.length === 0) return baseChartData;
    const leftIdx = baseChartData.findIndex((d) => d.date === zoomedRange.left);
    const rightIdx = baseChartData.findIndex((d) => d.date === zoomedRange.right);
    if (leftIdx === -1 || rightIdx === -1) return baseChartData;
    const start = Math.min(leftIdx, rightIdx);
    const end = Math.max(leftIdx, rightIdx);
    return baseChartData.slice(start, end + 1);
  }, [baseChartData, zoomedRange]);

  const compareMap = useMemo(() => {
    const map = new Map<string, number>();
    for (const obs of compareObservations) {
      map.set(obs.date, obs.value);
    }
    return map;
  }, [compareObservations]);

  const sortedCompare = useMemo(() => {
    return [...compareObservations].sort((a, b) => a.date.localeCompare(b.date));
  }, [compareObservations]);

  // Merge benchmark observations into display chart dataset cleanly
  const mergedChartData: Array<{
    date: string;
    value: number;
    compareValue: number | null;
    rawValue: number;
    rawCompareValue: number | null;
  }> = useMemo(() => {
    if (!displayChartData || displayChartData.length === 0) return [];

    const dataset = displayChartData.map((d) => ({
      date: d.date,
      value: d.value,
      compareValue: null as number | null,
      rawValue: d.value,
      rawCompareValue: null as number | null,
    }));

    if (compareId === 'none' || compareObservations.length === 0) {
      return dataset;
    }

    const getCompareVal = (targetDate: string): number | null => {
      if (compareMap.has(targetDate)) return compareMap.get(targetDate)!;
      if (sortedCompare.length === 0) return null;

      let low = 0;
      let high = sortedCompare.length - 1;
      let ans: number | null = null;

      while (low <= high) {
        const mid = Math.floor((low + high) / 2);
        if (sortedCompare[mid].date <= targetDate) {
          ans = sortedCompare[mid].value;
          low = mid + 1;
        } else {
          high = mid - 1;
        }
      }
      return ans;
    };

    const firstPrimary = dataset[0]?.value || 1;

    let firstCompare: number | null = null;
    for (const d of dataset) {
      const v = getCompareVal(d.date);
      if (v !== null) {
        firstCompare = v;
        break;
      }
    }
    if (firstCompare === null) firstCompare = 1;

    for (const item of dataset) {
      const compareVal = getCompareVal(item.date);
      const primaryRebased = firstPrimary !== 0 ? ((item.value - firstPrimary) / Math.abs(firstPrimary)) * 100 : 0;
      const compareRebased =
        compareVal !== null && firstCompare !== 0 ? ((compareVal - firstCompare) / Math.abs(firstCompare)) * 100 : null;

      item.rawCompareValue = compareVal;
      item.compareValue = isRebased
        ? compareRebased !== null
          ? Number(compareRebased.toFixed(2))
          : null
        : compareVal;

      if (isRebased) {
        item.value = Number(primaryRebased.toFixed(2));
      }
    }

    return dataset;
  }, [displayChartData, compareId, compareObservations, compareMap, sortedCompare, isRebased]);

  // Snap raw recession dates to exact dates present in mergedChartData so daily/weekly/monthly charts render all recession bands
  const activeRecessionSpans = useMemo(() => {
    if (!recessionSpans.length || !mergedChartData.length) return [];
    
    const chartDates = mergedChartData.map((d) => d.date);
    const minDate = chartDates[0];
    const maxDate = chartDates[chartDates.length - 1];

    const activeSpans: { start: string; end: string }[] = [];

    for (const span of recessionSpans) {
      if (span.end < minDate || span.start > maxDate) continue;

      let startMatch = chartDates.find((d) => d >= span.start);
      let endMatch = [...chartDates].reverse().find((d) => d <= span.end);

      if (!startMatch) startMatch = minDate;
      if (!endMatch) endMatch = maxDate;

      if (startMatch <= endMatch) {
        activeSpans.push({ start: startMatch, end: endMatch });
      }
    }

    return activeSpans;
  }, [recessionSpans, mergedChartData]);

  // Pearson Correlation calculation for pairwise benchmark comparison
  const correlationData = useMemo(() => {
    if (compareId === 'none' || !mergedChartData || mergedChartData.length < 5) return null;

    const validPairs: { x: number; y: number }[] = [];
    for (const item of mergedChartData) {
      const xVal = isRebased ? item.rawValue : item.value;
      const yVal = isRebased ? item.rawCompareValue : item.compareValue;
      if (xVal !== undefined && xVal !== null && yVal !== undefined && yVal !== null) {
        validPairs.push({ x: xVal, y: yVal });
      }
    }

    if (validPairs.length < 5) return null;

    const n = validPairs.length;
    const meanX = validPairs.reduce((acc, p) => acc + p.x, 0) / n;
    const meanY = validPairs.reduce((acc, p) => acc + p.y, 0) / n;

    let num = 0;
    let denX = 0;
    let denY = 0;

    for (const p of validPairs) {
      const dx = p.x - meanX;
      const dy = p.y - meanY;
      num += dx * dy;
      denX += dx * dx;
      denY += dy * dy;
    }

    if (denX === 0 || denY === 0) return { r: 0, label: 'Neutral' };
    const r = num / Math.sqrt(denX * denY);

    let label = 'Neutral';
    if (r >= 0.6) label = 'Strong Positive';
    else if (r >= 0.25) label = 'Moderate Positive';
    else if (r <= -0.6) label = 'Strong Inverse';
    else if (r <= -0.25) label = 'Moderate Inverse';

    return { r: Number(r.toFixed(2)), label };
  }, [mergedChartData, compareId, isRebased]);

  // 5. Cross-Asset Correlation Heatmap Calculation (Option 1 - Bottom Strip)
  const crossAssetCorrelations = useMemo(() => {
    if (!rawTimeframeData || rawTimeframeData.length < 5) return [];

    const HEATMAP_BENCHMARKS = [
      { id: 'SP500', label: 'S&P 500' },
      { id: 'IQ12260', label: 'Gold' },
      { id: 'DGS10', label: '10Y Yield' },
      { id: 'DTWEXBGS', label: 'USD Index' },
      { id: 'VIXCLS', label: 'VIX' },
    ];

    return HEATMAP_BENCHMARKS.map((bm) => {
      const bmObs = heatmapData[bm.id] || [];
      if (!bmObs.length) return { id: bm.id, label: bm.label, r: null, status: 'N/A' };

      const bmMap = new Map<string, number>();
      for (const o of bmObs) bmMap.set(o.date, o.value);

      const pairs: { x: number; y: number }[] = [];
      for (const pt of rawTimeframeData) {
        const yVal = bmMap.get(pt.date);
        if (yVal !== undefined && yVal !== null) {
          pairs.push({ x: pt.value, y: yVal });
        }
      }

      if (pairs.length < 5) return { id: bm.id, label: bm.label, r: null, status: 'N/A' };

      const n = pairs.length;
      const meanX = pairs.reduce((sum, p) => sum + p.x, 0) / n;
      const meanY = pairs.reduce((sum, p) => sum + p.y, 0) / n;

      let num = 0;
      let denX = 0;
      let denY = 0;
      for (const p of pairs) {
        const dx = p.x - meanX;
        const dy = p.y - meanY;
        num += dx * dy;
        denX += dx * dx;
        denY += dy * dy;
      }

      if (denX === 0 || denY === 0) return { id: bm.id, label: bm.label, r: 0, status: 'Neutral' };
      const r = num / Math.sqrt(denX * denY);
      const roundedR = Number(r.toFixed(2));

      let status = 'Neutral';
      if (roundedR >= 0.5) status = 'Strong Positive';
      else if (roundedR >= 0.2) status = 'Moderate Positive';
      else if (roundedR <= -0.5) status = 'Strong Inverse';
      else if (roundedR <= -0.2) status = 'Moderate Inverse';

      return { id: bm.id, label: bm.label, r: roundedR, status };
    });
  }, [rawTimeframeData, heatmapData]);

  // Compute PERIOD CHANGE dynamically over the active chart timeframe
  const displayChange = useMemo(() => {
    if (!displayChartData || displayChartData.length < 2) return '0.00%';
    const firstPoint = displayChartData[0];
    const lastPoint = displayChartData[displayChartData.length - 1];
    
    if (!firstPoint || !lastPoint || firstPoint.value === 0) return '0.00%';

    const isRateOrPercent = 
      (activeItem.unit || '').toLowerCase().includes('percent') || 
      (activeItem.unit || '').toLowerCase().includes('yield') ||
      (activeItem.unit || '').toLowerCase().includes('rate');

    if (isRateOrPercent) {
      const diff = lastPoint.value - firstPoint.value;
      return `${diff >= 0 ? '+' : ''}${diff.toFixed(2)}%`;
    } else {
      const pctChange = ((lastPoint.value - firstPoint.value) / Math.abs(firstPoint.value)) * 100;
      return `${pctChange >= 0 ? '+' : ''}${pctChange.toFixed(2)}%`;
    }
  }, [displayChartData, activeItem.unit]);

  const handleZoom = () => {
    if (refAreaLeft && refAreaRight && refAreaLeft !== refAreaRight) {
      let [left, right] = [refAreaLeft, refAreaRight];
      const leftIdx = baseChartData.findIndex((d) => d.date === left);
      const rightIdx = baseChartData.findIndex((d) => d.date === right);
      if (leftIdx > rightIdx) {
        [left, right] = [right, left];
      }
      setZoomedRange({ left, right });
    }
    setRefAreaLeft('');
    setRefAreaRight('');
  };

  const analysisOverview = activeSeriesMeta?.analysis_overview || (activeItem as any)?.analysis_overview || activeItem?.description || `${activeItem?.name} (${activeItem?.fred_series_id}) is a key ${activeItem?.category?.toLowerCase()} macroeconomic series.`;
  const impactRising = activeSeriesMeta?.impact_rising || (activeItem as any)?.impact_rising || 'Elevates upward momentum in its core economic dimension, influencing benchmark valuations and central bank policy expectations.';
  const impactFalling = activeSeriesMeta?.impact_falling || (activeItem as any)?.impact_falling || 'Signals deceleration in its underlying dimension, shifting capital toward defensive assets and market safety.';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-full overflow-hidden select-none">
      {/* Sidebar - Indicator List */}
      <div className="lg:col-span-4 xl:col-span-3 h-full overflow-hidden flex flex-col space-y-3 lg:border-r border-[var(--border-color)] lg:pr-5">
        {/* Search */}
        <div className="relative shrink-0">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search indicator in database..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-main)] pl-9 pr-3 py-1.5 text-xs text-[var(--text-main)] placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap items-center gap-1 pb-1 shrink-0">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`text-xs px-1.5 py-0.5 transition-colors ${
                selectedCategory === cat.id
                  ? 'font-bold text-[var(--text-main)] underline underline-offset-4'
                  : 'text-gray-500 hover:text-[var(--text-main)]'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Indicator Item List */}
        <div className="space-y-1 flex-1 overflow-y-auto pr-1">
          {filteredIndicators.length === 0 ? (
            <div className="text-xs text-gray-500 py-4 px-2">No indicators found.</div>
          ) : (
            filteredIndicators.map((item) => {
              const isSelected = item.fred_series_id === selectedId;
              return (
                <button
                  key={item.fred_series_id}
                  onClick={() => handleSelectId(item.fred_series_id)}
                  className={`w-full text-left px-3 py-2 rounded-md transition-all text-xs font-mono flex items-center justify-between border ${
                    isSelected
                      ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-500 text-blue-600 dark:text-blue-400 font-bold shadow-sm'
                      : 'border-transparent text-[var(--text-main)] hover:bg-[var(--bg-subtle)]'
                  }`}
                >
                  <div className="truncate pr-2">
                    <div className="truncate font-sans font-medium text-xs">{item.name}</div>
                    <div className="text-[10px] text-gray-400 uppercase font-mono">{item.fred_series_id}</div>
                  </div>
                  <div className="text-[10px] uppercase tracking-wider text-gray-400 shrink-0">
                    {item.category}
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Main Detail & Chart Panel */}
      <div className="lg:col-span-8 xl:col-span-9 h-full overflow-y-auto lg:pl-2 pr-2 space-y-6 pb-8">
        <div className="space-y-4">
          <div>
            <div className="text-xs font-mono text-gray-400 uppercase tracking-wider">
              {activeItem.category} • {stalenessText || activeItem.frequency || 'Monthly'} • {activeItem.fred_series_id}
            </div>

            <h3 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight mt-1">
              {activeItem.name}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 font-light leading-relaxed">
              {activeItem.description || activeSeriesMeta?.description || ''}
            </p>
          </div>

          {/* Stats Row with Percentile Rank & Release Info */}
          <div className="flex flex-wrap items-center gap-8 py-2 border-y border-[var(--border-color)] text-xs font-mono">
            <div>
              <div className="text-gray-400 text-[10px]">CURRENT VALUE</div>
              <div className="text-lg font-bold text-slate-900 dark:text-white">
                {loading ? '...' : displayValue}
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-[10px]">PERIOD CHANGE</div>
              <div className="text-lg font-bold text-slate-900 dark:text-white">
                {loading ? '...' : displayChange}
              </div>
            </div>

            {/* 1. Historical Percentile Rank Badge */}
            {percentileRank !== null && (
              <div>
                <div className="text-gray-400 text-[10px]">HISTORICAL PERCENTILE</div>
                <div className="text-lg font-bold text-slate-900 dark:text-white">
                  {percentileRank}th
                </div>
              </div>
            )}

            {/* 2. Release Schedule & Next Release Badge */}
            {activeSeriesMeta?.release_info?.next_release && (
              <div>
                <div className="text-gray-400 text-[10px]">NEXT RELEASE</div>
                <div className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span>{activeSeriesMeta.release_info.next_release}</span>
                  {activeSeriesMeta.release_info.days_until !== null && activeSeriesMeta.release_info.days_until !== undefined && (
                    <span className={`text-[10px] font-normal font-sans ${
                      activeSeriesMeta.release_info.days_until <= 3
                        ? 'text-amber-600 dark:text-amber-400 font-semibold'
                        : 'text-gray-400 dark:text-gray-500'
                    }`}>
                      ({activeSeriesMeta.release_info.days_until === 0 ? 'Today' : `in ${activeSeriesMeta.release_info.days_until}d`})
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* 3. Consensus vs. Actual Surprise Badge */}
            {activeSeriesMeta?.latest_consensus && (
              <div>
                <div className="text-gray-400 text-[10px] uppercase">
                  RELEASE SURPRISE ({activeSeriesMeta.latest_consensus.period || 'Latest'})
                </div>
                <div className="text-lg font-bold text-slate-900 dark:text-white flex items-baseline gap-2 font-mono">
                  <span>
                    {activeSeriesMeta.latest_consensus.actual}
                    {activeSeriesMeta.latest_consensus.unit}
                  </span>
                  <span className="text-xs text-gray-500 font-normal">
                    vs {activeSeriesMeta.latest_consensus.consensus}
                    {activeSeriesMeta.latest_consensus.unit} exp
                  </span>
                  {activeSeriesMeta.latest_consensus.surprise_delta !== null && (
                    <span className="text-[11px] font-semibold text-slate-700 dark:text-slate-300">
                      ({activeSeriesMeta.latest_consensus.surprise_delta > 0 ? '+' : ''}
                      {activeSeriesMeta.latest_consensus.surprise_delta}
                      {activeSeriesMeta.latest_consensus.unit})
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Benchmark Correlation Metric Chip */}
            {activeBenchmark && compareId !== 'none' && (
              <div className="border-l border-[var(--border-color)] pl-6">
                <div className="text-gray-400 text-[10px] uppercase">
                  CORRELATION ({activeBenchmark.label})
                </div>
                <div className="text-lg font-bold text-slate-900 dark:text-white">
                  {loadingCompare
                    ? '...'
                    : correlationData
                    ? `${correlationData.r >= 0 ? '+' : ''}${correlationData.r} (${correlationData.label})`
                    : 'N/A'}
                </div>
              </div>
            )}
          </div>

          {/* Chart Controls Bar & Chart Container */}
          <div className="space-y-3 pt-1">
            {/* Minimalist Controls Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs font-mono">
              {/* Benchmark Overlay Selector & Technical Transformations */}
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-gray-400 text-[11px]">Compare:</span>
                <div className="flex items-center gap-1 border border-[var(--border-color)] p-0.5 rounded bg-[var(--bg-main)]">
                  {BENCHMARKS.map((b) => {
                    const isActive = compareId === b.id;
                    return (
                      <button
                        key={b.id}
                        onClick={() => setCompareId(b.id)}
                        className={`px-2 py-0.5 rounded text-[11px] transition-all font-mono ${
                          isActive
                            ? 'font-bold bg-gray-200 dark:bg-slate-800 text-[var(--text-main)] shadow-sm'
                            : 'text-gray-500 hover:text-[var(--text-main)]'
                        }`}
                        style={isActive && b.id !== 'none' ? { color: COMPARISON_COLOR } : {}}
                      >
                        {b.label}
                      </button>
                    );
                  })}

                  {/* Fixed-size Searchable Custom Indicator Dropdown */}
                  <div className="relative" ref={compareDropdownRef}>
                    <button
                      onClick={() => setIsCompareOpen(!isCompareOpen)}
                      className={`w-32 sm:w-36 px-2 py-0.5 rounded text-[11px] font-mono transition-all flex items-center justify-between gap-1 border ${
                        isCustomActive
                          ? 'font-bold bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white border-slate-400'
                          : 'border-transparent text-gray-500 hover:text-[var(--text-main)]'
                      }`}
                      style={isCustomActive ? { color: COMPARISON_COLOR } : {}}
                      title={isCustomActive ? activeCustomSeries?.name || compareId : 'Select custom indicator'}
                    >
                      <span className="truncate flex-1 text-left">
                        {isCustomActive ? activeCustomSeries?.name || compareId : 'Custom...'}
                      </span>
                      <ChevronDown className={`w-3 h-3 shrink-0 opacity-60 transition-transform ${isCompareOpen ? 'rotate-180' : ''}`} />
                    </button>

                    {isCompareOpen && (
                      <div className="absolute top-full right-0 sm:left-0 mt-1.5 w-64 bg-[var(--bg-main)] border border-[var(--border-color)] shadow-xl rounded-md p-2 z-50 space-y-1.5 font-mono">
                        <div className="relative">
                          <input
                            type="text"
                            placeholder="Type to search..."
                            value={compareSearchQuery}
                            onChange={(e) => setCompareSearchQuery(e.target.value)}
                            className="w-full px-2 py-1 pr-6 text-[11px] bg-[var(--bg-subtle)] border border-[var(--border-color)] rounded focus:outline-none focus:border-blue-500 text-[var(--text-main)]"
                            autoFocus
                          />
                          {compareSearchQuery && (
                            <button
                              onClick={() => setCompareSearchQuery('')}
                              className="absolute right-2 top-1.5 text-gray-400 hover:text-gray-600 text-xs"
                            >
                              ✕
                            </button>
                          )}
                        </div>
                        <div className="max-h-48 overflow-y-auto space-y-0.5 pr-1">
                          {filteredCustomSeries.length === 0 ? (
                            <div className="text-[11px] text-gray-400 p-2">No matching indicators</div>
                          ) : (
                            filteredCustomSeries.map((s) => {
                              const isSel = compareId === s.fred_series_id;
                              return (
                                <button
                                  key={s.fred_series_id}
                                  onClick={() => {
                                    setCompareId(s.fred_series_id);
                                    setIsCompareOpen(false);
                                  }}
                                  className={`w-full text-left px-2 py-1.5 rounded text-[11px] transition-colors flex items-center justify-between ${
                                    isSel
                                      ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-bold'
                                      : 'hover:bg-[var(--bg-subtle)] text-[var(--text-main)]'
                                  }`}
                                >
                                  <span className="truncate pr-2">{s.name}</span>
                                  <span className="text-[9px] text-gray-400 font-mono shrink-0">{s.fred_series_id}</span>
                                </button>
                              );
                            })
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* 4. Technical Transformation Strip (Nominal | % Rebased | YoY %) */}
                <div className="flex items-center gap-1 border border-[var(--border-color)] p-0.5 rounded bg-[var(--bg-main)]">
                  {(['nominal', 'rebased', 'yoy'] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setTransformMode(mode)}
                      className={`px-2 py-0.5 rounded text-[11px] transition-all font-mono ${
                        transformMode === mode
                          ? 'font-bold bg-gray-200 dark:bg-slate-800 text-[var(--text-main)] shadow-sm'
                          : 'text-gray-500 hover:text-[var(--text-main)]'
                      }`}
                    >
                      {mode === 'nominal' ? 'Nominal' : mode === 'rebased' ? '% Rebased' : 'YoY %'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Timeframe & Zoom Reset Controls */}
              <div className="flex items-center space-x-3 self-end sm:self-auto">
                {zoomedRange && (
                  <button
                    onClick={() => setZoomedRange(null)}
                    className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    Reset Zoom ✕
                  </button>
                )}

                <div className="flex items-center space-x-3">
                  {['1Y', 'YTD', '3Y', '5Y', '10Y', 'ALL'].map((tf) => (
                    <button
                      key={tf}
                      onClick={() => handleSelectTimeframe(tf)}
                      className={`transition-colors ${
                        timeframe === tf
                          ? 'font-bold text-[var(--text-main)] underline underline-offset-4 decoration-2 decoration-blue-600'
                          : 'text-gray-500 hover:text-[var(--text-main)]'
                      }`}
                    >
                      {tf}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Chart Area */}
            <div
              className="relative h-[calc(100vh-440px)] min-h-[380px] w-full cursor-crosshair"
              onDoubleClick={() => setZoomedRange(null)}
            >
              {/* Threshold Descriptions Badge at Very Top-Left of Chart */}
              {TRIGGER_THRESHOLDS[activeItem.fred_series_id] && (
                <div className="absolute top-4 left-16 sm:left-20 z-20 flex flex-wrap items-center gap-2 font-mono text-[10px] pointer-events-none">
                  {TRIGGER_THRESHOLDS[activeItem.fred_series_id].map((t, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-1.5 font-mono text-[10px]"
                    >
                      <span className="w-2 h-0.5 rounded-full" style={{ backgroundColor: t.color }}></span>
                      <span style={{ color: t.color }} className="font-semibold">{t.label}</span>
                    </div>
                  ))}
                </div>
              )}

              {loading ? (
                <div className="h-full w-full flex items-center justify-center text-xs font-mono text-gray-500">
                  Loading database observations...
                </div>
              ) : mergedChartData.length === 0 ? (
                <div className="h-full w-full flex items-center justify-center text-xs font-mono text-gray-500">
                  No observations found in database for series {selectedId}.
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart
                    data={mergedChartData}
                    onMouseDown={(e) => e && e.activeLabel && setRefAreaLeft(e.activeLabel)}
                    onMouseMove={(e) => refAreaLeft && e && e.activeLabel && setRefAreaRight(e.activeLabel)}
                    onMouseUp={handleZoom}
                    onDoubleClick={() => setZoomedRange(null)}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                    <XAxis dataKey="date" stroke="#94A3B8" tick={{ fontSize: 11, fill: '#64748B' }} />
                    
                    {/* Primary Left Y-Axis */}
                    <YAxis
                      yAxisId="left"
                      stroke="#94A3B8"
                      tick={{ fontSize: 11, fill: '#64748B' }}
                      domain={['auto', 'auto']}
                      tickFormatter={(v) => (isRebased || isYoY ? `${v}%` : v)}
                    />

                    {/* Benchmark Right Y-Axis */}
                    {compareId !== 'none' && !isRebased && (
                      <YAxis
                        yAxisId="right"
                        orientation="right"
                        stroke={COMPARISON_COLOR}
                        tick={{ fontSize: 11, fill: COMPARISON_COLOR }}
                        domain={['auto', 'auto']}
                      />
                    )}

                    <Tooltip
                      content={
                        <CustomTooltip
                          activeItem={activeItem}
                          activeBenchmark={activeBenchmark}
                          isRebased={isRebased}
                          isYoY={isYoY}
                        />
                      }
                    />

                    {/* 2. NBER Recession Shading Overlay */}
                    {activeRecessionSpans.map((span, idx) => (
                      <ReferenceArea
                        key={`rec-${idx}`}
                        yAxisId="left"
                        x1={span.start}
                        x2={span.end}
                        fill="#64748B"
                        fillOpacity={0.12}
                        stroke="none"
                      />
                    ))}

                    {/* 3. Critical Trigger / Threshold Lines */}
                    {TRIGGER_THRESHOLDS[activeItem.fred_series_id]?.map((t, idx) => (
                      <ReferenceLine
                        key={`trig-${idx}`}
                        yAxisId="left"
                        y={t.y}
                        stroke={t.color}
                        strokeDasharray="3 3"
                        strokeWidth={1.5}
                      />
                    ))}

                    {/* Primary Series Line */}
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="value"
                      name={activeItem.name}
                      stroke="#2563EB"
                      strokeWidth={2}
                      dot={false}
                      connectNulls={true}
                    />

                    {/* Benchmark Overlay Line */}
                    {compareId !== 'none' && (
                      <Line
                        yAxisId={isRebased ? 'left' : 'right'}
                        type="monotone"
                        dataKey="compareValue"
                        name={activeBenchmark?.label || compareId}
                        stroke={COMPARISON_COLOR}
                        strokeWidth={2}
                        dot={false}
                        connectNulls={true}
                      />
                    )}

                    {refAreaLeft && refAreaRight && (
                      <ReferenceArea
                        yAxisId="left"
                        x1={refAreaLeft}
                        x2={refAreaRight}
                        strokeOpacity={0.3}
                        fill="#2563EB"
                        fillOpacity={0.25}
                      />
                    )}

                    <Brush
                      dataKey="date"
                      height={30}
                      stroke="#2563EB"
                      fill="var(--bg-main)"
                      tickFormatter={() => ''}
                    >
                      <ComposedChart data={mergedChartData}>
                        <Line
                          type="monotone"
                          dataKey="value"
                          stroke="#2563EB"
                          strokeWidth={1}
                          dot={false}
                          connectNulls={true}
                        />
                      </ComposedChart>
                    </Brush>
                  </ComposedChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>

        {/* Detailed Analytical Context & Market Impact Section */}
        <div className="pt-5 border-t border-[var(--border-color)] space-y-4 font-mono text-xs">
          <div className="text-gray-400 uppercase tracking-wider text-[10px]">
            Detailed Indicator Analysis & Market Context
          </div>

          {/* Deep Overview Paragraph */}
          <div className="font-sans space-y-1">
            <div className="font-semibold text-slate-900 dark:text-white text-xs font-mono">
              Indicator Overview & Economic Significance
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed font-light">
              {analysisOverview}
            </p>
          </div>

          {/* Market Impact Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 font-sans">
            <div className="space-y-1">
              <div className="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5 text-xs font-mono">
                <span className="text-blue-600 dark:text-blue-400">▲</span> Rising Trend (Upside Impact)
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                {impactRising}
              </p>
            </div>

            <div className="space-y-1">
              <div className="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5 text-xs font-mono">
                <span className="text-blue-600 dark:text-blue-400">▼</span> Falling Trend (Downside Impact)
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                {impactFalling}
              </p>
            </div>
          </div>
        </div>

        {/* 5. Cross-Asset Correlation Heatmap (Option 1 - Bottom Analytical Strip) */}
        <div className="pt-6 border-t border-[var(--border-color)] space-y-3 font-mono text-xs">
          <div className="text-gray-400 uppercase tracking-wider text-[10px] flex items-center justify-between">
            <span>Cross-Asset Correlation Heatmap ({timeframe})</span>
            <span className="text-[10px] font-normal text-gray-500">Pairwise Pearson vs. Benchmark Universe</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-1">
            {crossAssetCorrelations.map((bm) => {
              const r = bm.r;
              let colorClasses = 'border-[var(--border-color)] bg-[var(--bg-main)] text-gray-400 dark:text-gray-500';
              if (r !== null) {
                const absR = Math.abs(r);
                if (absR >= 0.5) {
                  colorClasses = 'border-slate-400 dark:border-slate-600 bg-slate-100/80 dark:bg-slate-800/80 text-[var(--text-main)] font-semibold';
                } else if (absR >= 0.25) {
                  colorClasses = 'border-[var(--border-color)] bg-slate-50/50 dark:bg-slate-900/40 text-[var(--text-main)]';
                } else {
                  colorClasses = 'border-[var(--border-color)] bg-transparent text-gray-400 dark:text-gray-500';
                }
              }

              return (
                <div
                  key={bm.id}
                  className={`p-2.5 rounded border transition-all flex flex-col justify-between font-mono ${colorClasses}`}
                >
                  <div className="text-[10px] font-bold tracking-tight text-gray-500 dark:text-gray-400 uppercase">
                    {bm.label}
                  </div>
                  <div className="mt-1 flex items-baseline justify-between">
                    <span className="text-base font-bold">
                      {r !== null ? `${r >= 0 ? '+' : ''}${r}` : 'N/A'}
                    </span>
                    <span className="text-[9px] opacity-75 font-sans">
                      {bm.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
