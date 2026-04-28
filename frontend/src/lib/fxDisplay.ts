import type { ExchangeRatesInfo } from './types';

const FX_ORDER = ['MYR', 'SGD', 'THB', 'IDR', 'BND', 'PHP'] as const;

export type FxStatusTone = 'neutral' | 'notice' | 'warning';

export type FxRatesUserCopy = {
  tone: FxStatusTone;
  title: string;
  body: string;
};

function formatAsOfLabel(value: string | null): string | null {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Maps backend ``exchange_rates_info`` into short, non-technical copy for the ASEAN UI.
 * Raw ``message`` may contain Python exceptions — never show it verbatim to end users.
 */
export function fxRatesUserCopy(
  exchangeRates: Record<string, number>,
  info: ExchangeRatesInfo | null,
  asOf: string | null = null,
): FxRatesUserCopy {
  const hasMyr = Number.isFinite(Number(exchangeRates.MYR)) && Number(exchangeRates.MYR) > 0;
  const hasAny = Object.keys(exchangeRates).length > 0;

  if (!hasAny || !hasMyr) {
    return {
      tone: 'warning',
      title: 'Exchange rates incomplete',
      body:
        'We could not load a usable USD/MYR rate from the server. The chart stays in USD; the MYR view stays off until rates return.',
    };
  }

  if (!info) {
    return {
      tone: 'neutral',
      title: 'How MYR is estimated',
      body:
        'Regional prices are converted to USD on the server. The MYR column multiplies those USD amounts by USD/MYR from the same refresh.',
    };
  }

  if (info.used_static_fallback || info.provider === 'static') {
    return {
      tone: 'warning',
      title: 'Illustrative exchange rates',
      body:
        'The live currency service did not return rates in time, so MYR amounts use fixed reference values for comparison only. Treat them as directional, not market-exact.',
    };
  }

  const m = (info.message || '').toLowerCase();
  if (info.provider === 'fixer.io' && (m.includes('stale') || m.includes('disk cache'))) {
    const asOfLabel = formatAsOfLabel(asOf);
    return {
      tone: 'notice',
      title: asOfLabel ? `Exchange rates as of ${asOfLabel}` : 'Latest available exchange rates',
      body: '',
    };
  }

  if (info.provider === 'fixer.io') {
    return {
      tone: 'neutral',
      title: 'Rates from Fixer.io',
      body:
        'USD/MYR and related crosses come from Fixer.io (EUR-based feed converted to per-USD on the server), cached for the day to limit API usage.',
    };
  }

  if (info.provider === 'exchangerate.host') {
    return {
      tone: 'neutral',
      title: 'Rates from backup service',
      body:
        'When no Fixer.io key is configured, we use an alternate public FX feed for USD/MYR. Values refresh with each comparison load.',
    };
  }

  if (info.provider === 'none') {
    return {
      tone: 'warning',
      title: 'Rate source unavailable',
      body:
        'The server did not attach FX metadata for this response. If MYR looks wrong, reload after a moment or check the API.',
    };
  }

  return {
    tone: 'neutral',
    title: 'How MYR is estimated',
    body:
      'Regional prices are converted to USD on the server. The MYR column multiplies those USD amounts by USD/MYR from the same refresh.',
  };
}

export function fxRatesOrderedEntries(exchangeRates: Record<string, number>): [string, number][] {
  const out: [string, number][] = [];
  const seen = new Set<string>();
  for (const code of FX_ORDER) {
    const v = exchangeRates[code];
    if (v != null && Number.isFinite(Number(v))) {
      out.push([code, Number(v)]);
      seen.add(code);
    }
  }
  for (const [k, v] of Object.entries(exchangeRates)) {
    if (k === 'USD' || seen.has(k)) continue;
    if (typeof v === 'number' && Number.isFinite(v)) {
      out.push([k, v]);
    }
  }
  return out;
}

export function formatFxRateCell(code: string, value: number): string {
  if (code === 'IDR') return `${code}: ${value.toFixed(0)}`;
  if (code === 'MYR') return `${code}: ${value.toFixed(4)}`;
  return `${code}: ${value.toFixed(2)}`;
}
