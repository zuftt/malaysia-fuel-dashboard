import { useMemo, useState } from 'react';
import type { FuelPrice, PopularCar } from '../lib/types';
import { POPULAR_CARS_BASE } from '../lib/constants';
import { formatDateDDMMMYYYY } from '../lib/formatters';
import { Disclaimer } from './Disclaimer';

type Props = {
  prices: FuelPrice | null;
};

export function BudiCalculator({ prices }: Props) {
  const [budiKmDay, setBudiKmDay] = useState(40);
  const [budiTankSize, setBudiTankSize] = useState(45);
  const [budiConsumption, setBudiConsumption] = useState(8.5);
  const [budiCarModel, setBudiCarModel] = useState('myvi');

  const popularCars = useMemo<PopularCar[]>(() => {
    const custom: PopularCar = {
      id: 'custom',
      name: 'Other (manual)',
      category: 'Custom',
      tank: budiTankSize,
      consumption: budiConsumption,
      quota: 200,
    };
    return [...POPULAR_CARS_BASE, custom];
  }, [budiTankSize, budiConsumption]);

  const selectedCar = popularCars.find((c) => c.id === budiCarModel) || popularCars[0];

  const tank = selectedCar.tank;
  const consumption = selectedCar.consumption;
  const quota = selectedCar.quota;
  const litresDay = (budiKmDay / 100) * consumption;
  const litresMonth = litresDay * 30;
  const kmPerTank = consumption > 0 ? (tank / consumption) * 100 : 0;
  const refuelsMonth = tank > 0 ? litresMonth / tank : 0;
  const quotaFinishDay = litresDay > 0 ? Math.ceil(quota / litresDay) : null;
  const staysWithinQuota = litresMonth <= quota;

  const budiPriceRaw = prices?.ron95_subsidized;
  const marketPriceRaw = prices?.ron95_market;
  const hasOfficial =
    budiPriceRaw != null &&
    marketPriceRaw != null &&
    Number.isFinite(Number(budiPriceRaw)) &&
    Number.isFinite(Number(marketPriceRaw)) &&
    Number(budiPriceRaw) > 0 &&
    Number(marketPriceRaw) > 0;

  const budiPrice = hasOfficial ? Number(budiPriceRaw) : 0;
  const marketPrice = hasOfficial ? Number(marketPriceRaw) : 0;

  const litresSubsidised = Math.min(litresMonth, quota);
  const litresMarket = Math.max(0, litresMonth - quota);
  const costSubsidised = hasOfficial ? litresSubsidised * budiPrice : 0;
  const costMarket = hasOfficial ? litresMarket * marketPrice : 0;
  const costTotal = hasOfficial ? costSubsidised + costMarket : 0;
  const costIfAllMarket = hasOfficial ? litresMonth * marketPrice : 0;
  const savings = hasOfficial ? costIfAllMarket - costTotal : 0;

  const priceWeekLabel = prices?.date_announced
    ? formatDateDDMMMYYYY(prices.date_announced)
    : 'latest official row';

  return (
    <div className="panel p-4 sm:p-5">
      <div className="mb-5">
        <Disclaimer title="How eligibility & estimates work" tone="amber" icon="warning">
          <p>
            This calculator gives an <strong>estimate</strong> based on average-style consumption figures. Actual quota
            usage depends on driving conditions, vehicle load, and your habits. Eligibility for BUDI95 is determined by
            the Government of Malaysia via MySubsidi, not by this tool.
          </p>
          <p className="mt-2">
            Eligibility info:{' '}
            <a
              href="https://subsidi.gov.my/"
              className="text-[#0a0a0a] underline decoration-current decoration-1 underline-offset-2 hover:decoration-[#c24300]"
              target="_blank"
              rel="noopener noreferrer"
            >
              Subsidi Kerajaan (official portal)
            </a>{' '}
            and{' '}
            <a
              href="https://www.mof.gov.my/"
              className="text-[#0a0a0a] underline decoration-current decoration-1 underline-offset-2 hover:decoration-[#c24300]"
              target="_blank"
              rel="noopener noreferrer"
            >
              Ministry of Finance Malaysia
            </a>
            . This page does not verify accounts.
          </p>
        </Disclaimer>
      </div>

      {!hasOfficial ? (
        <p className="text-[13px] text-[#3a2600] bg-[#fdf6e9] border-l-2 border-[#c24300] px-3 py-2">
          Data temporarily unavailable. We need both subsidised and market RON 95 from the API before this calculator
          can run.
        </p>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 mb-6">
            <label className="cell-label sm:col-span-2">
              Vehicle
              <select
                className="mt-1 w-full border border-[#1a1a1a] px-2.5 py-2 text-sm bg-white mono focus:outline-none focus:ring-2 focus:ring-[#c24300] focus:ring-offset-1 focus:ring-offset-[#fafaf7] focus:border-[#c24300]"
                value={budiCarModel}
                onChange={(e) => setBudiCarModel(e.target.value)}
              >
                {(() => {
                  const groups = new Map<string, PopularCar[]>();
                  for (const car of popularCars) {
                    const brand = car.id === 'custom' ? 'Other' : car.name.split(' ')[0];
                    if (!groups.has(brand)) groups.set(brand, []);
                    groups.get(brand)!.push(car);
                  }
                  return [...groups.entries()].map(([brand, cars]) => (
                    <optgroup key={brand} label={brand}>
                      {cars.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}{c.years ? ` (${c.years})` : ''} — {c.category} · {c.tank}L tank · {c.consumption} L/100 km
                        </option>
                      ))}
                    </optgroup>
                  ));
                })()}
              </select>
            </label>

            <label className="cell-label">
              Daily distance (km)
              <input
                type="number"
                min={0}
                className="mt-1 w-full border border-[#1a1a1a] px-2.5 py-2 text-sm bg-white mono tabular-nums focus:outline-none focus:ring-2 focus:ring-[#c24300] focus:ring-offset-1 focus:ring-offset-[#fafaf7] focus:border-[#c24300]"
                value={budiKmDay}
                onChange={(e) => {
                  const raw = e.target.value;
                  if (raw === '') {
                    setBudiKmDay(0);
                    return;
                  }
                  const normalized = String(Number(raw));
                  e.target.value = normalized;
                  setBudiKmDay(Number(normalized) || 0);
                }}
              />
            </label>

            {budiCarModel === 'custom' && (
              <>
                <label className="cell-label">
                  Tank size (L)
                  <input
                    type="number"
                    min={1}
                    className="mt-1 w-full border border-[#1a1a1a] px-2.5 py-2 text-sm bg-white mono tabular-nums focus:outline-none focus:ring-2 focus:ring-[#c24300] focus:ring-offset-1 focus:ring-offset-[#fafaf7] focus:border-[#c24300]"
                    value={budiTankSize}
                    onChange={(e) => {
                      const raw = e.target.value;
                      if (raw === '') {
                        setBudiTankSize(1);
                        return;
                      }
                      const normalized = String(Number(raw));
                      e.target.value = normalized;
                      setBudiTankSize(Number(normalized) || 1);
                    }}
                  />
                </label>
                <label className="cell-label">
                  Consumption (L/100 km)
                  <input
                    type="number"
                    min={0.1}
                    step={0.1}
                    className="mt-1 w-full border border-[#1a1a1a] px-2.5 py-2 text-sm bg-white mono tabular-nums focus:outline-none focus:ring-2 focus:ring-[#c24300] focus:ring-offset-1 focus:ring-offset-[#fafaf7] focus:border-[#c24300]"
                    value={budiConsumption}
                    onChange={(e) => {
                      const raw = e.target.value;
                      if (raw === '') {
                        setBudiConsumption(0.1);
                        return;
                      }
                      const normalized = String(Number(raw));
                      e.target.value = normalized;
                      setBudiConsumption(Number(normalized) || 0.1);
                    }}
                  />
                </label>
              </>
            )}
          </div>

          {budiCarModel !== 'custom' && (
            <div className="flex flex-wrap items-stretch gap-0 -space-x-px mb-6">
              <span className="mono text-[11px] tracking-[0.08em] uppercase border border-[#1a1a1a] bg-white px-3 py-1.5 text-[#0a0a0a]">
                {selectedCar.name}
              </span>
              <span className="mono text-[11px] tracking-[0.08em] uppercase border border-[#1a1a1a] bg-white px-3 py-1.5 text-[#4b4b48]">
                Tank <strong className="text-[#0a0a0a] ml-1">{selectedCar.tank}L</strong>
              </span>
              <span className="mono text-[11px] tracking-[0.08em] uppercase border border-[#1a1a1a] bg-white px-3 py-1.5 text-[#4b4b48]">
                Use <strong className="text-[#0a0a0a] ml-1">{selectedCar.consumption} L/100km</strong>
              </span>
              <span className="mono text-[11px] tracking-[0.08em] uppercase border border-[#1a1a1a] bg-[#0a0a0a] px-3 py-1.5 text-[#fafaf7]">
                Quota {selectedCar.quota}L/mo
              </span>
            </div>
          )}

          <p className="text-[11px] mono tracking-[0.04em] text-[#6b6b68] mb-4 border-l-2 border-[#1a1a1a] pl-3 py-1">
            Subsidised RON 95 RM {budiPrice.toFixed(2)}/L · market RON 95 RM {marketPrice.toFixed(2)}/L · week {priceWeekLabel} · quota assumption {quota}L/mo.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 -space-x-px -space-y-px">
            <div className="border border-[#1a1a1a] bg-white p-4 relative">
              <span className="absolute top-2 right-2 mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#6b6b68]">
                Est
              </span>
              <div className="cell-label mb-3">Litres per month</div>
              <p className="serif text-[34px] leading-none font-semibold text-[#0a0a0a] tabular-nums">
                {litresMonth.toFixed(1)}
                <span className="text-[16px] font-normal text-[#6b6b68] ml-1">L</span>
              </p>
              <p className="text-[12px] text-[#4b4b48] mt-3 leading-relaxed">
                ≈ {refuelsMonth.toFixed(1)} full fills on a {tank}L tank ({kmPerTank.toFixed(0)} km per tank).
              </p>
            </div>

            <div className="border border-[#1a1a1a] bg-white p-4 relative">
              <span className="absolute top-2 right-2 mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#6b6b68]">
                Est
              </span>
              <div className="cell-label mb-3">Quota used by day</div>
              <p className="serif text-[34px] leading-none font-semibold text-[#0a0a0a] tabular-nums">
                {quotaFinishDay == null ? 'No usage' : `Day ${quotaFinishDay}`}
              </p>
              <p className="text-[12px] text-[#4b4b48] mt-3 leading-relaxed">
                {quotaFinishDay == null
                  ? `No fuel usage is projected, so the ${quota}L monthly quota is not consumed.`
                  : staysWithinQuota
                    ? `You stay within the monthly limit. At this usage, you would finish the ${quota}L quota around day ${quotaFinishDay}.`
                    : `You will finish the ${quota}L monthly quota by day ${quotaFinishDay}. Extra litres are priced at market rate in this model.`}
              </p>
            </div>

            <div className="border border-[#1a1a1a] bg-white p-4 relative">
              <span className="absolute top-2 right-2 mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#6b6b68]">
                Est
              </span>
              <div className="cell-label mb-3">Monthly cost</div>
              <p className="serif text-[34px] leading-none font-semibold text-[#0a0a0a] tabular-nums">
                RM {costTotal.toFixed(0)}
              </p>
              <div className="mt-3 text-[11px] mono tabular-nums space-y-1 text-[#4b4b48]">
                <p>
                  <span className="inline-block w-2 h-2 bg-[#166534] mr-2 align-middle" aria-hidden />
                  RM {costSubsidised.toFixed(2)} · {litresSubsidised.toFixed(1)}L × {budiPrice.toFixed(2)}
                </p>
                {litresMarket > 0 && (
                  <p>
                    <span className="inline-block w-2 h-2 bg-[#c24300] mr-2 align-middle" aria-hidden />
                    RM {costMarket.toFixed(2)} · {litresMarket.toFixed(1)}L × {marketPrice.toFixed(2)}
                  </p>
                )}
              </div>
            </div>

            <div className="border border-[#1a1a1a] bg-[#0a0a0a] text-[#fafaf7] p-4 relative">
              <span className="absolute top-2 right-2 mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#c24300]">
                Est
              </span>
              <div className="mono text-[11px] font-semibold tracking-[0.06em] uppercase text-[#ff6b35] mb-2">Monthly Savings</div>
              <p className="serif text-[38px] leading-none font-semibold text-[#ff6b35] tabular-nums">
                RM {savings.toFixed(0)}
              </p>
              <p className="text-[13px] text-[#c5c5c0] mt-3 leading-relaxed">
                vs. RM {costIfAllMarket.toFixed(0)} if you paid full market price
              </p>
            </div>
          </div>

          <div className="mt-6">
            <Disclaimer title="Data freshness & privacy" tone="neutral">
              <p>
                If BUDI95 eligibility rules or the subsidised rate change, we aim to update this copy within 24 hours.
                This page does not store what you type. Calculations run in your browser session only.
              </p>
            </Disclaimer>
          </div>
        </>
      )}
    </div>
  );
}
