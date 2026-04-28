/**
 * localStorage cache with TTLs tied to Malaysia's weekly fuel price cycle.
 *
 * MOF announces prices on Wednesday; effective Thursday 00:00 MYT (UTC+8).
 * Fuel prices are valid for exactly one week, so the right expiry for price
 * data is the *next* Thursday midnight MYT — not a fixed number of minutes.
 */

/** Next Thursday 00:00 MYT as a UTC Date. */
function nextThursdayMidnightMYT(): Date {
  // Work in MYT (UTC+8) to get the correct calendar day.
  const myt = new Date(
    new Date().toLocaleString('en-US', { timeZone: 'Asia/Kuala_Lumpur' }),
  );
  const day = myt.getDay(); // 0 Sun … 4 Thu … 6 Sat
  // If today IS Thursday, next effective Thursday is 7 days away (current week
  // prices are already loaded; we don't want to bust the cache mid-Thursday).
  const daysAhead = ((4 - day + 7) % 7) || 7;
  myt.setDate(myt.getDate() + daysAhead);
  myt.setHours(0, 0, 0, 0);
  // Convert back to UTC.
  return new Date(myt.getTime() - 8 * 60 * 60 * 1000);
}

type TTLStrategy = 'weekly-thursday' | 'daily' | 'half-hour';

function expiresAt(strategy: TTLStrategy): number {
  const now = Date.now();
  if (strategy === 'weekly-thursday') return nextThursdayMidnightMYT().getTime();
  if (strategy === 'daily') return now + 24 * 60 * 60 * 1000;
  return now + 30 * 60 * 1000; // 30 min
}

interface CacheEntry<T> {
  data: T;
  cachedAt: number;
  expiresAt: number;
}

export function cacheWrite<T>(key: string, data: T, strategy: TTLStrategy): void {
  if (typeof window === 'undefined') return;
  try {
    const entry: CacheEntry<T> = { data, cachedAt: Date.now(), expiresAt: expiresAt(strategy) };
    localStorage.setItem(key, JSON.stringify(entry));
  } catch {
    // localStorage full or unavailable — silently skip.
  }
}

export function cacheRead<T>(key: string): T | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const entry = JSON.parse(raw) as CacheEntry<T>;
    if (Date.now() > entry.expiresAt) {
      localStorage.removeItem(key);
      return null;
    }
    return entry.data;
  } catch {
    return null;
  }
}

// Typed keys for every API call the dashboard makes.
export const CACHE_KEYS = {
  pricesLatest:   'rr_prices_latest',    // weekly-thursday
  pricesHistory:  'rr_prices_history',   // weekly-thursday
  pumpStations:   'rr_pump_stations',    // weekly-thursday (Shell scrapes weekly)
  aseanCompare:   'rr_asean_compare',    // daily (seed data, no fixed cadence)
  news:           'rr_news',             // half-hour (articles refresh frequently)
} as const;
