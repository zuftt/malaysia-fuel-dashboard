import { useMemo, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
} from 'recharts';
import type { TrendData } from '../lib/types';
import { buildTrendChartRows } from '../lib/trendChart';
import { CHART_FONT, CHART_TOOLTIP_STYLE, FUEL_CHART_COLORS } from '../lib/chartTheme';
import { formatDateDDMMMYYYY } from '../lib/formatters';
import { DATA_GOV_MY_FUEL_CATALOGUE } from '../lib/constants';
import { useMediaQuery } from '../lib/useMediaQuery';
import { Disclaimer } from './Disclaimer';

type ChartFilter = 'all' | 'ron95' | 'ron97' | 'diesel';

type Props = {
  trends: TrendData[];
};

export function TrendChart({ trends }: Props) {
  const isMobile = useMediaQuery('(max-width: 639px)');
  const [chartFilter, setChartFilter] = useState<ChartFilter>(isMobile ? 'ron95' : 'all');
  const trendChartRows = useMemo(() => buildTrendChartRows(trends), [trends]);
  const chartHeight = isMobile ? 240 : 360;

  const lastDate =
    trendChartRows.length > 0 ? trendChartRows[trendChartRows.length - 1].date : null;
  const lastLabel = lastDate ? formatDateDDMMMYYYY(lastDate) : null;

  return (
    <div className="panel p-4 sm:p-5">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3 mb-4 pb-3 border-b border-[#e5e5e0]">
        <div className="mono text-[11px] text-[#6b6b68] tracking-[0.08em] uppercase space-y-0.5">
          {trendChartRows.length > 0 && (
            <p>
              {trendChartRows[0].date} → {trendChartRows[trendChartRows.length - 1].date} · {trendChartRows.length}{' '}
              weeks{lastLabel ? ` · last: ${lastLabel}` : ''}
            </p>
          )}
          <p>
            <a
              href={DATA_GOV_MY_FUEL_CATALOGUE}
              className="text-[#0a0a0a] underline decoration-[#1a1a1a] decoration-1 underline-offset-2 hover:decoration-[#c24300]"
              target="_blank"
              rel="noopener noreferrer"
            >
              Source: data.gov.my
            </a>
          </p>
        </div>
        <div className="flex flex-wrap -space-x-px" role="tablist" aria-label="Chart fuel filter">
          {(['all', 'ron95', 'ron97', 'diesel'] as const).map((filter) => (
            <button
              key={filter}
              type="button"
              role="tab"
              aria-selected={chartFilter === filter}
              onClick={() => setChartFilter(filter)}
              className="tab-btn"
            >
              {filter === 'all' ? 'All' : filter === 'ron95' ? 'RON 95' : filter === 'ron97' ? 'RON 97' : 'Diesel'}
            </button>
          ))}
        </div>
      </div>

      {trendChartRows.length > 0 ? (
        <>
          <ResponsiveContainer width="100%" height={chartHeight}>
            <LineChart data={trendChartRows} margin={{ top: 8, right: 12, left: 4, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: CHART_FONT.xs, fill: '#64748b' }}
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={['auto', 'auto']}
                tick={{ fontSize: CHART_FONT.xs, fill: '#64748b' }}
                tickLine={false}
                axisLine={false}
                width={44}
                label={{
                  value: 'RM/litre',
                  angle: -90,
                  position: 'insideLeft',
                  offset: 4,
                  style: { fill: '#94a3b8', fontSize: CHART_FONT.xs },
                }}
              />
              <Tooltip
                formatter={(value: number | string, name: string) => {
                  if (value == null || value === '') return ['—', name];
                  const n = Number(value);
                  if (!Number.isFinite(n)) return ['—', name];
                  return [`RM ${n.toFixed(2)}/litre`, name];
                }}
                labelFormatter={(label) => `Week: ${label}`}
                contentStyle={{
                  background: 'rgba(255,255,255,0.96)',
                  border: CHART_TOOLTIP_STYLE.border,
                  borderRadius: CHART_TOOLTIP_STYLE.borderRadius,
                  fontSize: CHART_TOOLTIP_STYLE.fontSize,
                }}
              />
              <Legend wrapperStyle={{ fontSize: CHART_FONT.base, paddingTop: 10 }} iconType="line" />
              {(chartFilter === 'all' || chartFilter === 'ron95') && (
                <Line
                  type="monotone"
                  dataKey="ron95"
                  name="RON 95 (Market)"
                  stroke={FUEL_CHART_COLORS.ron95}
                  strokeWidth={2.5}
                  dot={false}
                  connectNulls
                />
              )}
              {(chartFilter === 'all' || chartFilter === 'ron97') && (
                <Line
                  type="monotone"
                  dataKey="ron97"
                  name="RON 97"
                  stroke={FUEL_CHART_COLORS.ron97}
                  strokeWidth={2.5}
                  dot={false}
                  connectNulls
                />
              )}
              {(chartFilter === 'all' || chartFilter === 'diesel') && (
                <Line
                  type="monotone"
                  dataKey="diesel"
                  name="Diesel"
                  stroke={FUEL_CHART_COLORS.diesel}
                  strokeWidth={2.5}
                  dot={false}
                  connectNulls
                />
              )}
            </LineChart>
          </ResponsiveContainer>

          <details className="disclosure mt-6 border border-[#e5e5e0] bg-[#fafaf7]">
            <summary className="flex items-center gap-2 px-3 py-2 mono text-[11px] tracking-[0.14em] uppercase font-semibold text-[#0a0a0a]">
              <span className="chev text-[#6b6b68] text-xs leading-none" aria-hidden>›</span>
              View data as table
            </summary>
            <div className="px-3 pb-3 pt-1">
              <p className="text-[12px] text-[#6b6b68] mb-2">
                Same numbers as the chart. Empty cells mean that grade was not in the history row for that week.
              </p>
              <div className="overflow-x-auto">
                <table className="terminal">
                  <caption className="sr-only">Weekly RM per litre by fuel grade</caption>
                  <thead>
                    <tr>
                      <th>Week</th>
                      <th className="text-right">RON 95 (Market)</th>
                      <th className="text-right">RON 97</th>
                      <th className="text-right">Diesel</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...trendChartRows].reverse().map((row) => (
                      <tr key={row.date}>
                        <td className="whitespace-nowrap">{row.date}</td>
                        <td className="mono tabular-nums text-right">
                          {row.ron95 != null && Number.isFinite(row.ron95) ? row.ron95.toFixed(2) : '—'}
                        </td>
                        <td className="mono tabular-nums text-right">
                          {row.ron97 != null && Number.isFinite(row.ron97) ? row.ron97.toFixed(2) : '—'}
                        </td>
                        <td className="mono tabular-nums text-right">
                          {row.diesel != null && Number.isFinite(row.diesel) ? row.diesel.toFixed(2) : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </details>
        </>
      ) : (
        <div className="h-80 flex items-center justify-center">
          <p className="text-[#4b4b48]">Data not yet available for this chart.</p>
        </div>
      )}
      <div className="mt-4">
        <Disclaimer title="About this chart" tone="neutral">
          <p>
            Values match the weekly levels published on data.gov.my. We do not smooth or interpolate missing weeks —
            gaps reflect gaps in the source. RON 95 shown here is the <strong>market ceiling price</strong>, not the
            subsidised BUDI95 pump price. See the Prices section above for a detailed comparison of both rates.
          </p>
        </Disclaimer>
      </div>
    </div>
  );
}
