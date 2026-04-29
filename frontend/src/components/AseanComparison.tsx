import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts';
import type { AseanCompareRow, ExchangeRatesInfo } from '../lib/types';
import { formatDateDDMMMYYYY, formatLocalMoney } from '../lib/formatters';
import { countryFlag } from '../lib/countryFlag';
import { ASEAN_BAR_COLORS, CHART_FONT, CHART_TOOLTIP_STYLE } from '../lib/chartTheme';
import { fxRatesOrderedEntries, fxRatesUserCopy } from '../lib/fxDisplay';
import { Disclaimer } from './Disclaimer';

type CompareFuel = 'RON95' | 'RON97' | 'Diesel';

type Props = {
  rows: AseanCompareRow[];
  exchangeRates: Record<string, number>;
  /** From compare API ``exchange_rates_info`` — provider, static fallback flag, human message. */
  exchangeRatesInfo?: ExchangeRatesInfo | null;
  updatedAt: string | null;
};

function fuelGradeLabel(ft: CompareFuel): string {
  if (ft === 'RON95') return 'RON 95';
  if (ft === 'RON97') return 'RON 97';
  return 'Diesel';
}

function formatMyr(value: number, digits = 2): string {
  return new Intl.NumberFormat('en-MY', {
    style: 'currency',
    currency: 'MYR',
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function AseanComparison({ rows, exchangeRates, exchangeRatesInfo = null, updatedAt }: Props) {
  const [compareFuel, setCompareFuel] = useState<CompareFuel>('RON95');
  const [currencyView, setCurrencyView] = useState<'USD' | 'MYR'>('MYR');

  const myrPerUsd = Number(exchangeRates.MYR);
  const canShowMyr = Number.isFinite(myrPerUsd) && myrPerUsd > 0;
  const fxAsAt =
    updatedAt && !Number.isNaN(new Date(updatedAt).getTime())
      ? formatDateDDMMMYYYY(new Date(updatedAt))
      : null;

  const compareFiltered = rows.filter(
    (r) => r.fuel_type === compareFuel && Number.isFinite(r.usd_price),
  );

  const fxUser = fxRatesUserCopy(exchangeRates, exchangeRatesInfo, updatedAt);
  const barData = [...compareFiltered]
    .map((r) => {
      // For MYR-denominated rows (Malaysia) use local_price directly — avoids MYR→USD→MYR
      // roundtrip that introduces FX drift vs the official data.gov.my figure.
      const myrL = r.currency === 'MYR' ? r.local_price : r.usd_price * myrPerUsd;
      const chartVal = currencyView === 'MYR' && canShowMyr ? myrL : r.usd_price;
      const localLabel = r.local_name || r.fuel_type;
      return {
        key: r.country,
        name: `${countryFlag(r.country)} ${r.country_name}`,
        localLabel,
        chartVal,
        subsidised: r.is_subsidised,
        myrL,
      };
    })
    .sort((a, b) => b.chartVal - a.chartVal);

  const tankL = 40;

  useEffect(() => {
    if (!canShowMyr && currencyView === 'MYR') setCurrencyView('USD');
  }, [canShowMyr, currencyView]);

  return (
    <div className="panel p-4 sm:p-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between mb-5 pb-4 border-b border-[#e5e5e0]">
        <div className="min-w-0">
          <p className="text-[13px] text-[#4b4b48] leading-relaxed">
            <strong>Showing {fuelGradeLabel(compareFuel)}</strong> — nearest equivalent grade per ASEAN country, converted to{' '}
            {currencyView === 'MYR' ? (
              <strong>Malaysian Ringgit (estimated)</strong>
            ) : (
              <strong>USD</strong>
            )}{' '}
            per litre using exchange rates below.
          </p>
          {updatedAt && (
            <p className="mono text-[11px] text-[#6b6b68] tracking-[0.08em] uppercase mt-2">
              Table and FX bundle last refreshed:{' '}
              {new Date(updatedAt).toLocaleString('en-GB', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          )}
          {canShowMyr && fxAsAt && (
            <p className="mono text-[11px] text-[#6b6b68] mt-1.5 tabular-nums tracking-[0.04em]">
              MYR per 1 USD: {myrPerUsd.toFixed(4)} as at {fxAsAt}
            </p>
          )}
        </div>
        <div className="flex flex-col gap-2 items-stretch sm:items-end">
          <div className="flex flex-wrap justify-end -space-x-px" role="tablist" aria-label="Chart currency">
            {(['USD', 'MYR'] as const).map((cur) => (
              <button
                key={cur}
                type="button"
                role="tab"
                aria-selected={currencyView === cur}
                disabled={cur === 'MYR' && !canShowMyr}
                title={
                  cur === 'MYR' && !canShowMyr
                    ? 'MYR view needs a USD/MYR rate from the server'
                    : undefined
                }
                onClick={() => setCurrencyView(cur)}
                className={`tab-btn ${cur === 'MYR' && !canShowMyr ? 'opacity-40 cursor-not-allowed pointer-events-none' : ''}`}
              >
                {cur}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap justify-end -space-x-px" role="tablist" aria-label="Fuel grade filter">
            {(['RON95', 'RON97', 'Diesel'] as const).map((ft) => (
              <button
                key={ft}
                type="button"
                role="tab"
                aria-selected={compareFuel === ft}
                onClick={() => setCompareFuel(ft)}
                className="tab-btn"
              >
                {fuelGradeLabel(ft)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {barData.length > 0 ? (
        <div className="mb-8">
          <ResponsiveContainer width="100%" height={Math.min(420, 56 + barData.length * 48)}>
            <BarChart layout="vertical" data={barData} margin={{ top: 8, right: 28, left: 8, bottom: 8 }}>
              <XAxis
                type="number"
                dataKey="chartVal"
                tick={{ fontSize: CHART_FONT.sm, fill: '#6b6b68' }}
                tickFormatter={(v) =>
                  currencyView === 'MYR' && canShowMyr
                    ? `RM${Number(v).toFixed(2)}`
                    : `$${Number(v).toFixed(2)}`
                }
                domain={[0, 'auto']}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={150}
                tick={{ fontSize: CHART_FONT.sm, fill: '#4b4b48' }}
              />
              <Tooltip
                formatter={(v: number | string, _name: string, props: { payload?: { localLabel?: string } }) => {
                  const n = Number(v);
                  if (!Number.isFinite(n)) return ['—', ''];
                  const label = props.payload?.localLabel || '';
                  if (currencyView === 'MYR' && canShowMyr) {
                    return [`${formatMyr(n, 3)}/litre`, label];
                  }
                  return [`$${n.toFixed(3)}/litre`, label];
                }}
                contentStyle={CHART_TOOLTIP_STYLE}
              />
              <Bar dataKey="chartVal" radius={[0, 6, 6, 0]} barSize={26}>
                {barData.map((entry) => {
                  const isMalaysia = entry.key === 'MY';
                  const fill = isMalaysia
                    ? '#c24300'
                    : entry.subsidised
                    ? ASEAN_BAR_COLORS.subsidised
                    : ASEAN_BAR_COLORS.market;
                  return <Cell key={entry.key} fill={fill} />;
                })}
                <LabelList
                  dataKey="chartVal"
                  position="right"
                  offset={8}
                  className="mono"
                  fill="#4b4b48"
                  fontSize={11}
                  formatter={(value: number | string) => {
                    const n = Number(value);
                    if (!Number.isFinite(n)) return '';
                    if (currencyView === 'MYR' && canShowMyr) return `RM${n.toFixed(2)}`;
                    return `$${n.toFixed(2)}`;
                  }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="text-[13px] text-[#4b4b48] mt-2 leading-relaxed">
            The table below lists the same values as this chart, plus local pump prices where we have them.
          </p>
          <div className="flex flex-wrap gap-4 mono text-[11px] text-[#6b6b68] tracking-[0.08em] uppercase mt-3">
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-3 h-3 shrink-0" style={{ backgroundColor: '#c24300' }} />{' '}
              Malaysia
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-3 h-3 shrink-0" style={{ backgroundColor: ASEAN_BAR_COLORS.subsidised }} />{' '}
              Subsidised or controlled
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-3 h-3 shrink-0" style={{ backgroundColor: ASEAN_BAR_COLORS.market }} />{' '}
              Market retail
            </span>
          </div>
        </div>
      ) : (
        <div className="rounded-sm border border-dashed border-[#c4c4bf] bg-[#f4f4f0] px-5 py-8 text-center mb-8">
          <p className="mono text-[11px] tracking-[0.16em] uppercase text-[#6b6b68] mb-2">ASEAN comparison unavailable</p>
          <p className="text-[13px] text-[#4b4b48] max-w-lg mx-auto leading-relaxed">
            Regional comparison data is loading. Check back shortly.
          </p>
        </div>
      )}

      <div className="w-full min-w-0 overflow-x-auto">
        <table className="terminal min-w-full">
          <caption className="sr-only">
            ASEAN {fuelGradeLabel(compareFuel)}: local pump price and{' '}
            {currencyView === 'MYR' && canShowMyr ? 'estimated MYR from USD' : 'USD'} per litre, {tankL} litre tank
            total.
          </caption>
          <thead>
            <tr>
              <th scope="col">Country</th>
              <th scope="col">Local product</th>
              <th scope="col">Local pump</th>
              {currencyView === 'MYR' && canShowMyr ? (
                <>
                  <th scope="col">MYR/litre (est.)</th>
                  <th scope="col">{tankL}L tank MYR (est.)</th>
                </>
              ) : (
                <>
                  <th scope="col">USD/litre</th>
                  <th scope="col">{tankL}L tank USD</th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {compareFiltered.map((r) => {
              const myrL = canShowMyr ? (r.currency === 'MYR' ? r.local_price : r.usd_price * myrPerUsd) : 0;
              return (
                <tr key={r.country}>
                  <td className="font-medium text-[#0a0a0a]">
                    <span className="mr-2">{countryFlag(r.country)}</span>
                    {r.country_name}
                    {r.is_subsidised && (
                      <span className="ml-2 mono text-[9px] font-bold uppercase tracking-[0.12em] text-[#15803d] bg-[#ecfdf5] border border-[#bbf7d0] px-2 py-0.5">
                        subsidised
                      </span>
                    )}
                  </td>
                  <td className="text-[12px] text-[#4b4b48]">{r.local_name || r.fuel_type}</td>
                  <td className="mono tabular-nums">{formatLocalMoney(r.local_price, r.currency)}</td>
                  {currencyView === 'MYR' && canShowMyr ? (
                    <>
                      <td className="mono tabular-nums">{formatMyr(myrL, 2)}</td>
                      <td className="mono tabular-nums font-semibold text-[#0a0a0a]">{formatMyr(myrL * tankL, 0)}</td>
                    </>
                  ) : (
                    <>
                      <td className="mono tabular-nums">${r.usd_price.toFixed(3)}</td>
                      <td className="mono tabular-nums font-semibold text-[#0a0a0a]">
                        ${(r.usd_price * tankL).toFixed(2)}
                      </td>
                    </>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-10">
        <div>
          <h3 className="serif text-xl font-semibold text-[#0a0a0a] mb-1">Currency rates</h3>
          <p className="text-[13px] text-[#4b4b48] mb-3 leading-relaxed">
            How much local currency equals 1 US Dollar. We use these rates to convert each country&apos;s pump price into a comparable MYR figure.
          </p>
          <div className="mb-4 text-[13px] leading-relaxed" role="status">
            <p className="text-[#4b4b48]">{fxUser.title}</p>
            {fxUser.body ? <p className="text-[#4b4b48] mt-1">{fxUser.body}</p> : null}
          </div>
          {fxRatesOrderedEntries(exchangeRates).length > 0 ? (
            <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 -space-x-px -space-y-px mb-3">
              {fxRatesOrderedEntries(exchangeRates).map(([code, val]) => {
                const countryMap: Record<string, string> = {
                  'MYR': 'Malaysia',
                  'SGD': 'Singapore',
                  'THB': 'Thailand',
                  'IDR': 'Indonesia',
                  'BND': 'Brunei',
                  'PHP': 'Philippines',
                };
                return (
                  <li key={code} className="relative border border-[#1a1a1a] bg-white p-4">
                    <span className="absolute top-2 right-2 mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#6b6b68]">
                      Est
                    </span>
                    <div className="cell-label mb-2">{countryMap[code] || code}</div>
                    <p className="serif text-[28px] leading-none font-semibold text-[#0a0a0a] tabular-nums">
                      {code === 'IDR' ? val.toFixed(0) : val.toFixed(code === 'MYR' ? 4 : 2)}
                    </p>
                    <p className="text-[12px] text-[#4b4b48] mt-2 leading-relaxed">
                      1 USD = {code === 'IDR' ? val.toFixed(0) : val.toFixed(code === 'MYR' ? 4 : 2)} {code}
                    </p>
                  </li>
                );
              })}
            </ul>
          ) : null}
        </div>
      </div>

      <div className="mt-8 space-y-3">
        <Disclaimer title="Accuracy & grade-mapping warning" tone="amber" icon="warning" defaultOpen={false}>
          <p>
            <strong>Fuel grades differ between countries.</strong> “RON 95” here maps to Pertalite (RON 90) in
            Indonesia and Gasohol 95 in Thailand; Singapore retails RON 95 directly. The local product name for each
            row is shown in the table. Some countries may show older or placeholder figures when live feeds are not
            available yet.
          </p>
        </Disclaimer>
        <Disclaimer title="About MYR equivalents & sources" tone="neutral">
          <p>
            MYR equivalents multiply USD/litre by MYR per USD. They are estimates for comparison, not actual pump
            prices in those countries.
          </p>
          <p className="mt-2">
            <strong>Sources:</strong> per-country fields in our database (see architecture docs). Brunei and
            Philippines may use manual placeholder data until dedicated feeds land.
          </p>
        </Disclaimer>
      </div>
    </div>
  );
}
