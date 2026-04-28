export interface FuelPrice {
  date_announced: string;
  ron95_subsidized: number;
  ron95_market: number;
  ron97: number;
  diesel_peninsular: number;
  source?: string;
}

export interface TrendData {
  date: string;
  fuel_type?: string;
  local_price: number;
  global_reference?: number | null;
  subsidy_gap?: number | null;
}

export interface NewsArticle {
  id: number;
  title: string;
  source: string;
  source_url: string | null;
  announcement_date: string;
  announcement_type: string;
  content?: string | null;
}

export interface AseanCompareRow {
  country: string;
  country_name: string;
  fuel_type: string;
  local_name: string;
  local_price: number;
  currency: string;
  usd_price: number;
  is_subsidised: boolean;
  date: string;
  source: string;
  source_url: string | null;
}

/** From GET /api/v1/prices/compare — how FX rates were obtained (Fixer, exchangerate.host, or static). */
export interface ExchangeRatesInfo {
  provider: string;
  used_static_fallback: boolean;
  message: string;
}

/** Dated snapshot from GET /api/v1/prices/asean/history */
export interface AseanHistoryRow extends AseanCompareRow {
  usd_uses_latest_fx?: boolean;
}

export interface MyPumpPriceRow {
  station: string;
  location?: string;
  ron95_budi?: number | null;
  ron95?: number | null;
  ron97?: number | null;
  vpower?: number | null;
  ron100?: number | null;
  diesel?: number | null;
  diesel_b7?: number | null;
  updated_at?: string | null;
}

export type PopularCar = {
  id: string;
  name: string;
  category: string;
  tank: number;
  consumption: number;
  quota: number;
};
