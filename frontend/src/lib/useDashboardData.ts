import { useEffect, useState } from 'react';
import axios from 'axios';
import { API_URL, DATA_GOV_MY_FUEL_CATALOGUE, DATA_GOV_MY_FUEL_CSV } from './constants';
import { cacheRead, cacheWrite, CACHE_KEYS } from './cache';
import type {
  AseanCompareRow,
  ExchangeRatesInfo,
  FuelPrice,
  MyPumpPriceRow,
  NewsArticle,
  TrendData,
} from './types';

export interface PriceMeta {
  retrievedAt: string;
  sourceUrl: string;
  sourceCatalogueUrl: string;
}

interface PumpStationsPayload {
  data: MyPumpPriceRow[];
  count: number;
  timestamp: string;
}

export interface DashboardData {
  prices: FuelPrice | null;
  prevPrices: FuelPrice | null;
  priceMeta: PriceMeta | null;
  trends: TrendData[];
  articles: NewsArticle[];
  aseanRows: AseanCompareRow[];
  aseanRates: Record<string, number>;
  aseanRatesInfo: ExchangeRatesInfo | null;
  aseanUpdated: string | null;
  pumpRows: MyPumpPriceRow[];
  pumpRetrievedAt: string | null;
  loading: boolean;
  error: string | null;
}

const EMPTY: DashboardData = {
  prices: null,
  prevPrices: null,
  priceMeta: null,
  trends: [],
  articles: [],
  aseanRows: [],
  aseanRates: {},
  aseanRatesInfo: null,
  aseanUpdated: null,
  pumpRows: [],
  pumpRetrievedAt: null,
  loading: true,
  error: null,
};

/**
 * Shared dashboard data hook. Reads localStorage cache for instant paint,
 * then fetches in the background. Cache keys match `pages/index.tsx` so
 * both pages share the same source of truth without duplicate network.
 */
export function useDashboardData(): DashboardData {
  const [state, setState] = useState<DashboardData>(EMPTY);

  useEffect(() => {
    let cancelled = false;
    const req = { timeout: 25_000 };

    // Paint from cache immediately — no flash on cold start.
    const cached = {
      latest: cacheRead<Record<string, unknown>>(CACHE_KEYS.pricesLatest),
      history: cacheRead<TrendData[]>(CACHE_KEYS.pricesHistory),
      pump: cacheRead<PumpStationsPayload>(CACHE_KEYS.pumpStations),
      asean: cacheRead<Record<string, unknown>>(CACHE_KEYS.aseanCompare),
      news: cacheRead<NewsArticle[]>(CACHE_KEYS.news),
    };

    const initial: Partial<DashboardData> = {};
    let hasCachedData = false;

    if (cached.latest) {
      const payload = cached.latest;
      const row = (payload?.data ?? payload) as FuelPrice;
      initial.prices = row;
      if (typeof payload.source_url === 'string' && typeof payload.timestamp === 'string') {
        initial.priceMeta = {
          retrievedAt: payload.timestamp,
          sourceUrl: payload.source_url || DATA_GOV_MY_FUEL_CSV,
          sourceCatalogueUrl:
            typeof payload.source_catalogue_url === 'string'
              ? payload.source_catalogue_url
              : DATA_GOV_MY_FUEL_CATALOGUE,
        };
      }
      hasCachedData = true;
    }
    if (cached.history) {
      initial.trends = cached.history;
      hasCachedData = true;
    }
    if (cached.pump) {
      const rows = Array.isArray(cached.pump.data) ? cached.pump.data : [];
      initial.pumpRows = rows;
      if (typeof cached.pump.timestamp === 'string') initial.pumpRetrievedAt = cached.pump.timestamp;
      hasCachedData = true;
    }
    if (cached.asean) {
      const aseanPayload = cached.asean;
      initial.aseanRows = Array.isArray(aseanPayload.data)
        ? (aseanPayload.data as AseanCompareRow[])
        : [];
      initial.aseanRates =
        aseanPayload.exchange_rates && typeof aseanPayload.exchange_rates === 'object'
          ? (aseanPayload.exchange_rates as Record<string, number>)
          : {};
      const fxInfo = aseanPayload.exchange_rates_info;
      if (
        fxInfo &&
        typeof fxInfo === 'object' &&
        typeof (fxInfo as ExchangeRatesInfo).provider === 'string' &&
        typeof (fxInfo as ExchangeRatesInfo).used_static_fallback === 'boolean' &&
        typeof (fxInfo as ExchangeRatesInfo).message === 'string'
      ) {
        initial.aseanRatesInfo = fxInfo as ExchangeRatesInfo;
      }
      initial.aseanUpdated = (aseanPayload.updated_at as string) ?? null;
      hasCachedData = true;
    }
    if (cached.news) {
      initial.articles = cached.news;
      hasCachedData = true;
    }

    if (hasCachedData) {
      setState((prev) => ({ ...prev, ...initial, loading: false }));
    }

    const fetchData = async (background: boolean) => {
      try {
        const [priceRes, trendRes, newsRes, aseanRes, pumpRes] = await Promise.all([
          axios.get(`${API_URL}/api/v1/prices/latest`, req),
          axios.get(`${API_URL}/api/v1/prices/history?days=84`, req),
          axios
            .get(`${API_URL}/api/v1/news/latest?limit=9`, req)
            .catch(() => ({ data: { data: [] as NewsArticle[] } })),
          axios.get(`${API_URL}/api/v1/prices/compare`, req).catch(() => ({
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
          axios.get(`${API_URL}/api/v1/prices/pump-stations`, req).catch(() => ({
            data: { data: [] as MyPumpPriceRow[], count: 0, timestamp: '' } as PumpStationsPayload,
          })),
        ]);

        if (cancelled) return;

        const payload = priceRes.data as Record<string, unknown> | undefined;
        const row = (payload?.data ?? priceRes.data) as FuelPrice;

        let priceMeta: PriceMeta | null = null;
        if (
          payload &&
          typeof payload.source_url === 'string' &&
          typeof payload.timestamp === 'string'
        ) {
          priceMeta = {
            retrievedAt: payload.timestamp as string,
            sourceUrl: (payload.source_url as string) || DATA_GOV_MY_FUEL_CSV,
            sourceCatalogueUrl:
              typeof payload.source_catalogue_url === 'string'
                ? (payload.source_catalogue_url as string)
                : DATA_GOV_MY_FUEL_CATALOGUE,
          };
        }

        const trendData: TrendData[] = trendRes.data?.data ?? trendRes.data ?? [];
        const newsRows = newsRes.data?.data ?? [];
        const articles = Array.isArray(newsRows) ? newsRows : [];

        const aseanPayload = aseanRes.data ?? {};
        const aseanRows = Array.isArray(aseanPayload.data) ? aseanPayload.data : [];
        const aseanRates =
          aseanPayload.exchange_rates && typeof aseanPayload.exchange_rates === 'object'
            ? aseanPayload.exchange_rates
            : {};
        const fxInfo = aseanPayload.exchange_rates_info;
        let aseanRatesInfo: ExchangeRatesInfo | null = null;
        if (
          fxInfo &&
          typeof fxInfo === 'object' &&
          typeof (fxInfo as ExchangeRatesInfo).provider === 'string' &&
          typeof (fxInfo as ExchangeRatesInfo).used_static_fallback === 'boolean' &&
          typeof (fxInfo as ExchangeRatesInfo).message === 'string'
        ) {
          aseanRatesInfo = fxInfo as ExchangeRatesInfo;
        }
        const aseanUpdated = aseanPayload.updated_at ?? null;

        const pumpPayload = (pumpRes?.data ?? {}) as Partial<PumpStationsPayload>;
        const pumpRows = Array.isArray(pumpPayload.data) ? pumpPayload.data : [];
        const pumpRetrievedAt =
          typeof pumpPayload.timestamp === 'string' ? pumpPayload.timestamp : null;

        let prevPrices: FuelPrice | null = null;
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
            prevPrices = {
              date_announced: String(prevDate),
              ron95_subsidized: prevRon95?.local_price != null ? Number(prevRon95.local_price) : 0,
              ron95_market: prevMarketRon95 ?? 0,
              ron97: prevRon97?.local_price != null ? Number(prevRon97.local_price) : 0,
              diesel_peninsular:
                prevDiesel?.local_price != null ? Number(prevDiesel.local_price) : 0,
            };
          }
        }

        if (payload) cacheWrite(CACHE_KEYS.pricesLatest, payload, 'weekly-thursday');
        if (trendData.length) cacheWrite(CACHE_KEYS.pricesHistory, trendData, 'weekly-thursday');
        if (pumpRows.length) cacheWrite(CACHE_KEYS.pumpStations, pumpRes.data, 'weekly-thursday');
        if (aseanPayload.data) cacheWrite(CACHE_KEYS.aseanCompare, aseanPayload, 'daily');
        if (newsRows.length) cacheWrite(CACHE_KEYS.news, newsRows, 'half-hour');

        setState({
          prices: row,
          prevPrices,
          priceMeta,
          trends: trendData,
          articles,
          aseanRows,
          aseanRates,
          aseanRatesInfo,
          aseanUpdated,
          pumpRows,
          pumpRetrievedAt,
          loading: false,
          error: null,
        });
      } catch {
        if (!cancelled && !background) {
          setState((prev) => ({
            ...prev,
            loading: false,
            error: 'Data temporarily unavailable. Check that the API is running and try again.',
          }));
        }
      }
    };

    void fetchData(false);
    const interval = setInterval(() => void fetchData(true), 60_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return state;
}
