import { useState, useEffect } from 'react';
import Head from 'next/head';
import axios from 'axios';
import { API_URL, DATA_GOV_MY_FUEL_CATALOGUE, DATA_GOV_MY_FUEL_CSV } from '../lib/constants';
import type {
  FuelPrice,
  TrendData,
  NewsArticle,
  AseanCompareRow,
  ExchangeRatesInfo,
  MyPumpPriceRow,
} from '../lib/types';
import { formatPrice, formatDateDDMMMYYYY, formatDateLongEn } from '../lib/formatters';
import { FuelCard, type PriceChange } from '../components/FuelCard';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { AseanComparison } from '../components/AseanComparison';
import { TrendChart } from '../components/TrendChart';
import { BudiCalculator } from '../components/BudiCalculator';
import { NewsGrid } from '../components/NewsGrid';
import { FaqSection } from '../components/FaqSection';
import { Section } from '../components/Section';
import { Disclaimer } from '../components/Disclaimer';
import { PageSkeleton } from '../components/Skeleton';

/** One RM/litre cell per row (single grade per row; fields are mutually exclusive in practice). */
function formatPumpRowPrice(r: MyPumpPriceRow): string {
  const n = (v: unknown) =>
    v != null && Number.isFinite(Number(v)) ? formatPrice(Number(v)) : null;
  const chunks = [
    n(r.ron95_budi),
    n(r.ron95),
    n(r.ron97),
    n(r.vpower),
    n(r.ron100),
    n(r.diesel),
    n(r.diesel_b7),
  ].filter(Boolean) as string[];
  if (chunks.length === 0) return '—';
  return chunks.join(' · ');
}

function pumpGradeLabel(r: MyPumpPriceRow): string {
  const base = r.station || '—';
  if (r.location) return `${base} (${r.location})`;
  return base;
}

/** Malay SEO headline; uses MOF effective date when loaded, else today. */
function malaysiaFuelHeadlineParts(dateAnnounced: string | undefined): {
  fullTitle: string;
  dateLabel: string;
} {
  const dateLabel = dateAnnounced ? formatDateLongEn(dateAnnounced) : formatDateLongEn(new Date());
  const fullTitle = `Harga Minyak Malaysia Terkini (${dateLabel}) & BUDI95 Calculator`;
  return { fullTitle, dateLabel };
}

function fuelPageMetaDescription(marketRm: string, budiRm: string, year: number): string {
  return `Track the latest weekly fuel prices in Malaysia. See the gap between market rates (RM ${marketRm}) and your BUDI95 price (RM ${budiRm}). Use our ${year} Fuel Calculator to see how much the government is subsidizing your monthly commute.`;
}

type PriceMeta = {
  retrievedAt: string;
  sourceUrl: string;
  sourceCatalogueUrl: string;
};

type PumpStationsPayload = {
  data: MyPumpPriceRow[];
  count: number;
  timestamp: string;
};

export default function Home() {
  const [prices, setPrices] = useState<FuelPrice | null>(null);
  const [priceMeta, setPriceMeta] = useState<PriceMeta | null>(null);
  const [prevPrices, setPrevPrices] = useState<FuelPrice | null>(null);
  const [trends, setTrends] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [aseanRows, setAseanRows] = useState<AseanCompareRow[]>([]);
  const [aseanRates, setAseanRates] = useState<Record<string, number>>({});
  const [aseanRatesInfo, setAseanRatesInfo] = useState<ExchangeRatesInfo | null>(null);
  const [aseanUpdated, setAseanUpdated] = useState<string | null>(null);
  const [pumpRows, setPumpRows] = useState<MyPumpPriceRow[]>([]);
  const [pumpRetrievedAt, setPumpRetrievedAt] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const req = { timeout: 25_000 };

    const fetchData = async (background: boolean) => {
      try {
        if (!background) setLoading(true);
        const [priceRes, trendRes, newsRes, aseanRes, pumpRes] = await Promise.all([
          axios.get(`${API_URL}/api/v1/prices/latest`, req),
          axios.get(`${API_URL}/api/v1/prices/history?days=84`, req),
          axios
            .get(`${API_URL}/api/v1/news/latest?limit=9`, req)
            .catch(() => ({ data: { data: [] as NewsArticle[] } })),
          axios
            .get(`${API_URL}/api/v1/prices/compare`, req)
            .catch(() => ({
              data: {
                data: [] as AseanCompareRow[],
                exchange_rates: {},
                updated_at: null as string | null,
                exchange_rates_info: {
                  provider: 'none',
                  used_static_fallback: false,
                  message: 'Compare request failed; FX not loaded.',
                },
              },
            })),
          axios
            .get(`${API_URL}/api/v1/prices/pump-stations`, req)
            .catch(() => ({
              data: { data: [] as MyPumpPriceRow[], count: 0, timestamp: '' } as PumpStationsPayload,
            })),
        ]);

        if (cancelled) return;

        const payload = priceRes.data as Record<string, unknown> | undefined;
        const row = (payload?.data ?? priceRes.data) as FuelPrice;
        setPrices(row);

        if (payload && typeof payload.source_url === 'string' && typeof payload.timestamp === 'string') {
          setPriceMeta({
            retrievedAt: payload.timestamp as string,
            sourceUrl: (payload.source_url as string) || DATA_GOV_MY_FUEL_CSV,
            sourceCatalogueUrl:
              typeof payload.source_catalogue_url === 'string'
                ? (payload.source_catalogue_url as string)
                : DATA_GOV_MY_FUEL_CATALOGUE,
          });
        } else {
          setPriceMeta(null);
        }

        const trendData = trendRes.data?.data ?? trendRes.data ?? [];
        setTrends(trendData);

        const newsRows = newsRes.data?.data ?? [];
        setArticles(Array.isArray(newsRows) ? newsRows : []);

        const aseanPayload = aseanRes.data ?? {};
        setAseanRows(Array.isArray(aseanPayload.data) ? aseanPayload.data : []);
        setAseanRates(
          aseanPayload.exchange_rates && typeof aseanPayload.exchange_rates === 'object'
            ? aseanPayload.exchange_rates
            : {},
        );
        const fxInfo = aseanPayload.exchange_rates_info;
        if (
          fxInfo &&
          typeof fxInfo === 'object' &&
          typeof (fxInfo as ExchangeRatesInfo).provider === 'string' &&
          typeof (fxInfo as ExchangeRatesInfo).used_static_fallback === 'boolean' &&
          typeof (fxInfo as ExchangeRatesInfo).message === 'string'
        ) {
          setAseanRatesInfo(fxInfo as ExchangeRatesInfo);
        } else {
          setAseanRatesInfo(null);
        }
        setAseanUpdated(aseanPayload.updated_at ?? null);

        const pumpPayload = (pumpRes?.data ?? {}) as Partial<PumpStationsPayload>;
        const rows = Array.isArray(pumpPayload.data) ? pumpPayload.data : [];
        setPumpRows(rows);
        setPumpRetrievedAt(typeof pumpPayload.timestamp === 'string' ? pumpPayload.timestamp : null);

        if (trendData.length >= 2) {
          const dates = [...new Set(trendData.map((t: TrendData) => t.date))].sort().reverse();
          if (dates.length >= 2) {
            const prevDate = dates[1];
            const prevWeek = trendData.filter((t: TrendData) => t.date === prevDate);
            const prevRon97 = prevWeek.find((t: TrendData) => t.fuel_type === 'RON97');
            const prevDiesel = prevWeek.find((t: TrendData) => t.fuel_type === 'Diesel');
            const prevRon95 = prevWeek.find((t: TrendData) => t.fuel_type === 'RON95');
            const prevMarketRon95 =
              prevRon95?.global_reference != null && Number(prevRon95.global_reference) > 0
                ? Number(prevRon95.global_reference)
                : undefined;
            setPrevPrices({
              date_announced: String(prevDate),
              ron95_subsidized: prevRon95?.local_price != null ? Number(prevRon95.local_price) : 0,
              ron95_market: prevMarketRon95 ?? 0,
              ron97: prevRon97?.local_price != null ? Number(prevRon97.local_price) : 0,
              diesel_peninsular: prevDiesel?.local_price != null ? Number(prevDiesel.local_price) : 0,
            });
          }
        }

        setError(null);
      } catch (err) {
        console.error('Error fetching data:', err);
        if (!cancelled && !background) {
          setError('Data temporarily unavailable. Check that the API is running and try again.');
        }
      } finally {
        if (!cancelled && !background) setLoading(false);
      }
    };

    void fetchData(false);
    const interval = setInterval(() => void fetchData(true), 60_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (loading) {
    const { fullTitle: loadingTitle } = malaysiaFuelHeadlineParts(undefined);
    const y = new Date().getFullYear();
    return (
      <>
        <Head>
          <title>{`${loadingTitle} | RONradar`}</title>
          <meta name="description" content={fuelPageMetaDescription('3.87', '1.99', y)} />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        </Head>
        <PageSkeleton />
      </>
    );
  }

  if (error) {
    const { fullTitle: errorTitle } = malaysiaFuelHeadlineParts(undefined);
    const y = new Date().getFullYear();
    return (
      <>
        <Head>
          <title>{`${errorTitle} | RONradar`}</title>
          <meta name="description" content={fuelPageMetaDescription('3.87', '1.99', y)} />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        </Head>
        <div className="min-h-screen bg-[#fafaf7] text-[#0a0a0a] flex items-center justify-center px-6">
          <div className="max-w-xl w-full panel-heavy p-6">
            <p className="eyebrow mb-2">Error</p>
            <h2 className="serif text-2xl font-semibold tracking-tight mb-2">Data temporarily unavailable</h2>
            <p className="text-[13px] text-[#4b4b48] mb-4 leading-relaxed">{error}</p>
            <details className="disclosure text-[13px] text-[#4b4b48]">
              <summary className="cursor-pointer mono text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6b6b68] hover:text-[#0a0a0a]">
                Connection details
              </summary>
              <p className="mt-2 mono text-[11px] text-[#6b6b68] break-all">API base URL: {API_URL}</p>
            </details>
          </div>
        </div>
      </>
    );
  }

  const getChange = (current: number | undefined, previous: number | undefined): PriceChange => {
    const c = Number(current);
    const p = Number(previous);
    if (!Number.isFinite(c) || c <= 0) return null;
    if (!Number.isFinite(p) || p <= 0) return null;
    if (c === p) return { direction: 'flat', pct: '0.0', amountRm: '0.00' };
    const diff = c - p;
    const pctMag = Math.abs((diff / p) * 100);
    return {
      direction: diff > 0 ? 'up' : 'down',
      pct: pctMag.toFixed(1),
      amountRm: Math.abs(diff).toFixed(2),
    };
  };

  const retrievedLabel = (() => {
    if (!priceMeta?.retrievedAt) return 'not reported by API';
    const d = new Date(priceMeta.retrievedAt);
    if (Number.isNaN(d.getTime())) return 'not reported by API';
    return `${formatDateDDMMMYYYY(d)} at ${d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`;
  })();

  const sourceName = prices?.source?.trim() || 'data.gov.my fuel catalogue';
  const catalogueUrl = priceMeta?.sourceCatalogueUrl || DATA_GOV_MY_FUEL_CATALOGUE;

  /** BUDI95 vs Peninsular RON95 market ceiling (RM/L), for top-right chip. */
  const budiVsMarketGapRm = (() => {
    if (!prices) return null;
    const m = Number(prices.ron95_market);
    const s = Number(prices.ron95_subsidized);
    if (!Number.isFinite(m) || !Number.isFinite(s)) return null;
    const gap = m - s;
    if (gap < 1e-6) return null;
    return gap.toFixed(2);
  })();

  const fuelCardsConfig = [
    {
      name: 'RON 95 (market)',
      shortName: 'RON 95',
      price: formatPrice(prices?.ron95_market),
      prevPrice:
        prevPrices?.ron95_market != null && Number(prevPrices.ron95_market) > 0
          ? formatPrice(prevPrices.ron95_market)
          : null,
      badge: 'Market',
      change: getChange(prices?.ron95_market, prevPrices?.ron95_market),
      note: 'National market ceiling for RON 95 before targeted subsidy. Same series as data.gov.my.',
      variant: 'ron95' as const,
    },
    {
      name: 'RON 95 (BUDI95)',
      shortName: 'BUDI95',
      price: formatPrice(prices?.ron95_subsidized),
      prevPrice:
        prevPrices?.ron95_subsidized != null && Number(prevPrices.ron95_subsidized) > 0
          ? formatPrice(prevPrices.ron95_subsidized)
          : null,
      badge: 'Subsidised',
      change: getChange(prices?.ron95_subsidized, prevPrices?.ron95_subsidized),
      note: 'Subsidised pump price for eligible recipients. Eligibility is decided by the Government via MySubsidi, not this site.',
      variant: 'budi' as const,
    },
    {
      name: 'RON 97',
      shortName: 'RON 97',
      price: formatPrice(prices?.ron97),
      prevPrice:
        prevPrices?.ron97 != null && Number(prevPrices.ron97) > 0 ? formatPrice(prevPrices.ron97) : null,
      badge: 'Market',
      change: getChange(prices?.ron97, prevPrices?.ron97),
      note: 'Floats with global markets. Official weekly level from data.gov.my.',
      variant: 'ron97' as const,
    },
    {
      name: 'Diesel (Peninsular)',
      shortName: 'Diesel',
      price: formatPrice(prices?.diesel_peninsular),
      prevPrice:
        prevPrices?.diesel_peninsular != null && Number(prevPrices.diesel_peninsular) > 0
          ? formatPrice(prevPrices.diesel_peninsular)
          : null,
      badge: 'Market',
      change: getChange(prices?.diesel_peninsular, prevPrices?.diesel_peninsular),
      note: 'Retail diesel Peninsular Malaysia. Official weekly level from data.gov.my.',
      variant: 'diesel' as const,
    },
  ];

  const effectiveLabel = prices?.date_announced ? formatDateDDMMMYYYY(prices.date_announced) : '—';
  const asOfTodayLabel = formatDateDDMMMYYYY(new Date());
  const { fullTitle: seoTitleMain, dateLabel: seoDateLabel } = malaysiaFuelHeadlineParts(prices?.date_announced);
  const metaYear = new Date().getFullYear();
  const metaMarketRm =
    prices != null &&
    Number.isFinite(Number(prices.ron95_market)) &&
    Number(prices.ron95_market) > 0
      ? formatPrice(prices.ron95_market)
      : '3.87';
  const metaBudiRm =
    prices != null &&
    Number.isFinite(Number(prices.ron95_subsidized)) &&
    Number(prices.ron95_subsidized) > 0
      ? formatPrice(prices.ron95_subsidized)
      : '1.99';
  const seoDescription = fuelPageMetaDescription(metaMarketRm, metaBudiRm, metaYear);

  return (
    <>
      <Head>
        <title>{`${seoTitleMain} | RONradar`}</title>
        <meta name="description" content={seoDescription} />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </Head>

      <div className="bg-[#fafaf7] text-[#0a0a0a] min-h-screen flex flex-col">
        <Header />

        <main id="top" className="flex-1 px-3 sm:px-6 max-w-7xl mx-auto w-full pb-24 sm:pb-12 pt-16 space-y-10">
          <header className="pt-6 pb-4 border-b border-[#1a1a1a] rr-header-in">
            <div className="flex items-center gap-2 mb-2">
              <span className="eyebrow">Peninsular Malaysia</span>
              <span className="text-[#6b6b68] mono text-[10px]">/</span>
              <span className="mono text-[10px] tracking-[0.12em] uppercase text-[#6b6b68]">Weekly</span>
              <span className="text-[#6b6b68] mono text-[10px]">/</span>
              <span className="mono text-[10px] tracking-[0.12em] uppercase text-[#6b6b68]">MYR per litre</span>
            </div>
            <h1 className="serif text-3xl sm:text-[2.15rem] md:text-4xl lg:text-5xl font-semibold tracking-tight text-[#0a0a0a] leading-[1.08] max-w-5xl">
              Harga Minyak Malaysia Terkini{' '}
              <span className="whitespace-nowrap">({seoDateLabel})</span>{' '}
              & BUDI95 Calculator
            </h1>
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-x-6 gap-y-2 text-[12px]">
              <div className="flex flex-col">
                <span className="cell-label">Effective</span>
                <span className="mono tabular-nums text-[#0a0a0a] text-sm">{effectiveLabel}</span>
              </div>
              <div className="flex flex-col">
                <span className="cell-label">Refreshed</span>
                <span className="mono tabular-nums text-[#0a0a0a] text-sm">{retrievedLabel}</span>
              </div>
              <div className="flex flex-col">
                <span className="cell-label">Source</span>
                <span className="text-sm">
                  <a
                    href={catalogueUrl}
                    className="text-[#0a0a0a] underline decoration-[#1a1a1a] decoration-1 underline-offset-2 hover:decoration-[#c24300]"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {sourceName}
                  </a>
                </span>
              </div>
            </div>
          </header>

          <Section
            id="prices"
            eyebrow="prices"
            title="Berapa harga minyak hari ini?"
            description={
              <>
                As of{' '}
                <span className="whitespace-nowrap font-semibold text-[#0a0a0a]">{asOfTodayLabel}</span>, this row shows the
                fuel prices in Peninsular Malaysia that are currently published on data.gov.my. The Malaysian government announces weekly retail fuel prices (RON95, RON97, and diesel)
                every <strong>Wednesday.</strong>
              </>
            }
            bare
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
              {fuelCardsConfig.map((card) => (
                <FuelCard
                  key={card.name}
                  name={card.name}
                  shortName={card.shortName}
                  price={card.price}
                  prevPrice={card.prevPrice}
                  badge={card.badge}
                  change={card.change}
                  variant={card.variant}
                  marketGapRm={card.variant === 'budi' ? budiVsMarketGapRm : undefined}
                />
              ))}
            </div>
            <div className="mt-4 max-w-3xl">
              <Disclaimer title="About this price" tone="neutral">
                <div className="space-y-4">
                  {fuelCardsConfig.map((card) => (
                    <div key={card.variant}>
                      <p className="mono text-[10px] font-bold tracking-[0.12em] uppercase text-[#6b6b68] mb-1">
                        {card.shortName ?? card.name}
                      </p>
                      <p>{card.note}</p>
                    </div>
                  ))}
                  <p className="pt-2 border-t border-[#e5e5e0] mono text-[10px] tracking-[0.1em] uppercase text-[#6b6b68]">
                    Src:{' '}
                    <a
                      href={catalogueUrl}
                      className="text-[#0a0a0a] underline decoration-[#1a1a1a] decoration-1 underline-offset-2 hover:decoration-[#c24300]"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {sourceName}
                    </a>{' '}
                    · {retrievedLabel}
                  </p>
                </div>
              </Disclaimer>
            </div>
          </Section>

          <Section
            id="grades"
            eyebrow="Overview"
            title="Latest prices by grade"
            description="Selected station prices we've sampled — supplementary detail beyond the headline numbers above."
          >
            {pumpRows.length > 0 ? (
              <>
                <div className="w-full min-w-0 overflow-x-auto">
                  <table className="terminal terminal--grades min-w-[280px] w-full">
                    <thead>
                      <tr>
                        <th scope="col">Grade</th>
                        <th scope="col" className="text-right">
                          Price
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {pumpRows.slice(0, 36).map((r, idx) => (
                        <tr key={`${r.station}-${idx}`}>
                          <td className="pr-3 sm:pr-6">{pumpGradeLabel(r)}</td>
                          <td className="mono tabular-nums text-right pl-3 sm:pl-6">{formatPumpRowPrice(r)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mono text-[11px] text-[#6b6b68] mt-3 tracking-[0.08em] uppercase">
                  {pumpRetrievedAt ? `Retrieved ${formatDateDDMMMYYYY(pumpRetrievedAt)}` : 'No timestamp'}
                </p>
              </>
            ) : (
              <div className="rounded-sm border border-dashed border-[#c4c4bf] bg-[#f4f4f0] px-5 py-8 text-center">
                <p className="mono text-[11px] tracking-[0.16em] uppercase text-[#6b6b68] mb-2">Pump prices not available</p>
                <p className="text-[13px] text-[#4b4b48] max-w-lg mx-auto leading-relaxed">
                  We could not load station-level prices right now. Headline weekly prices above remain accurate.
                </p>
              </div>
            )}
          </Section>

          <Section
            id="asean"
            eyebrow="Comparison"
            title="ASEAN retail fuel comparison"
            description="How Malaysia compares with regional neighbours — fuel grades differ, so read the detail."
            bare
          >
            <AseanComparison
              rows={aseanRows}
              exchangeRates={aseanRates}
              exchangeRatesInfo={aseanRatesInfo}
              updatedAt={aseanUpdated}
            />
          </Section>

          <Section
            id="trend"
            eyebrow="History"
            title="Weekly price trend"
            description="Market price history per fuel grade, in RM/litre, matching weekly levels from data.gov.my."
            bare
          >
            <TrendChart trends={trends} />
          </Section>

          <Section
            id="calculator"
            eyebrow="Tool"
            title="BUDI95 quota calculator"
            description="Pick a vehicle profile and your daily distance to estimate your monthly subsidised-vs-market split."
            bare
          >
            <BudiCalculator prices={prices} />
          </Section>

          <Section
            id="news"
            eyebrow="Feed"
            title="Berita Terkini"
            description="Latest fuel-related headlines from Malaysian news sources via Google News RSS."
            bare
          >
            <NewsGrid articles={articles} />
          </Section>

          <Section
            id="faq"
            eyebrow="FAQ"
            title="Questions and limits"
            description="How prices are set, what RONradar does and doesn't do."
            bare
          >
            <FaqSection />
          </Section>
        </main>

        <Footer />
      </div>
    </>
  );

}