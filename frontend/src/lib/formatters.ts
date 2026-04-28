/** DD MMM YYYY (British-style month abbrev), e.g. 16 Apr 2026 */
export function formatDateDDMMMYYYY(iso: string | Date): string {
  const d = typeof iso === 'string' ? new Date(iso) : iso;
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

/** e.g. 24 April 2026 — full month for page titles and meta (SEO). */
export function formatDateLongEn(iso: string | Date): string {
  const d = typeof iso === 'string' ? new Date(iso) : iso;
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export function formatPrice(value: unknown): string {
  if (value === null || value === undefined) return '--';
  const num = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(num)) return '--';
  return num.toFixed(2);
}

export function formatLocalMoney(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat('en-MY', {
      style: 'currency',
      currency,
      minimumFractionDigits: currency === 'IDR' ? 0 : 2,
      maximumFractionDigits: currency === 'IDR' ? 0 : 2,
    }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency}`;
  }
}

export function formatRelativeMs(iso: string): string {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return '';
  const s = Math.floor((Date.now() - t) / 1000);
  if (s < 45) return 'Baru sahaja';
  if (s < 3600) return `${Math.max(1, Math.floor(s / 60))} minit lalu`;
  if (s < 86400) return `${Math.floor(s / 3600)} jam lalu`;
  if (s < 604800) return `${Math.floor(s / 86400)} hari lalu`;
  return new Date(iso).toLocaleDateString('ms-MY', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export function shortSourceLabel(source: string): string {
  if (source.startsWith('RSS · ')) return source.slice(6);
  return source;
}
