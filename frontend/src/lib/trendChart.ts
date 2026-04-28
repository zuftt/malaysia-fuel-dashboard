import type { TrendData } from './types';

/** Pivot API history (long format) into one row per week for Recharts. */
export function buildTrendChartRows(rows: TrendData[]) {
  const map = new Map<string, { date: string; ron95?: number; ron97?: number; diesel?: number }>();
  for (const row of rows) {
    const raw = String(row.date);
    const d = raw.includes('T') ? raw.split('T')[0] : raw;
    if (!map.has(d)) map.set(d, { date: d });
    const e = map.get(d)!;
    const ft = (row.fuel_type || '').toUpperCase();
    if (ft === 'RON95') {
      const marketPrice = Number(row.global_reference);
      e.ron95 = Number.isFinite(marketPrice) ? marketPrice : Number(row.local_price);
    } else if (ft === 'RON97') {
      const p = Number(row.local_price);
      if (Number.isFinite(p)) e.ron97 = p;
    } else if (ft === 'DIESEL') {
      const p = Number(row.local_price);
      if (Number.isFinite(p)) e.diesel = p;
    }
  }
  return Array.from(map.values()).sort((a, b) => a.date.localeCompare(b.date));
}
