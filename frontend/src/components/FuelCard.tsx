export type FuelCardVariant = 'ron95' | 'budi' | 'ron97' | 'diesel';

export type PriceChange = {
  direction: 'up' | 'down' | 'flat';
  pct: string;
  amountRm: string;
} | null;

type FuelCardProps = {
  name: string;
  shortName?: string;
  price: string;
  /** Previous week’s price (MYR/L, two decimals) — no date shown beside it. */
  prevPrice: string | null;
  badge: string;
  change: PriceChange;
  variant: FuelCardVariant;
  /**
   * BUDI95 only: RM/litre gap vs Peninsular RON95 market ceiling (shown top-right instead of weekly %).
   */
  marketGapRm?: string | null;
};

/*
 * RON95: yellow-500 #eab308 on stripe + price + badge ring; title + MARKET yellow-600 — barely darker so the shift is subtle.
 * RON97 stripe: #388E3C.
 */
const variantStripe: Record<FuelCardVariant, string> = {
  ron95: 'bg-[#eab308]',
  budi: 'bg-[#0b5cad]',
  ron97: 'bg-[#388E3C]',
  diesel: 'bg-[#334155]',
};

const variantBadge: Record<FuelCardVariant, string> = {
  ron95: 'text-[#ca8a04] border-[#eab308]',
  budi: 'text-[#0b5cad] border-[#0b5cad]',
  ron97: 'text-[#1b5e20] border-[#43a047]',
  diesel: 'text-[#334155] border-[#334155]',
};

/** Headline for the fuel label — high contrast on #fafaf7. */
const variantTitle: Record<FuelCardVariant, string> = {
  ron95: 'text-[#ca8a04]',
  budi: 'text-[#075985]',
  ron97: 'text-[#14532d]',
  diesel: 'text-[#0f172a]',
};

/** Main RM/litre figure — clearly tied to each grade. */
const variantPrice: Record<FuelCardVariant, string> = {
  ron95: 'text-[#eab308]',
  budi: 'text-[#0369a1]',
  ron97: 'text-[#15803d]',
  diesel: 'text-[#334155]',
};

export function FuelCard({
  name,
  shortName,
  price,
  prevPrice,
  badge,
  change,
  variant,
  marketGapRm,
}: FuelCardProps) {
  const priceOk = price !== '--';
  const primaryLabel = (shortName ?? name).trim();

  const budiGapRm =
    variant === 'budi' && marketGapRm != null && String(marketGapRm).trim() !== '' ? String(marketGapRm).trim() : null;

  return (
    <article className="panel panel-elevate relative flex min-w-0 flex-col overflow-visible">
      <span aria-hidden className={`absolute inset-x-0 top-0 z-[1] h-[3px] ${variantStripe[variant]}`} />

      <div className="relative z-[2] px-2.5 sm:px-4 pt-3 sm:pt-4 pb-3 sm:pb-4 flex flex-col gap-2 sm:gap-3">
        {/* Grid: second column is max-content so RM gap / % chip never collapses on narrow flex (mobile). */}
        <header className="grid grid-cols-[minmax(0,1fr)_max-content] gap-x-2 gap-y-1 items-start sm:gap-x-3">
          <div className="min-w-0">
            <h3
              className={`serif text-base sm:text-lg md:text-xl font-bold tracking-tight leading-[1.15] ${variantTitle[variant]}`}
            >
              {primaryLabel}
            </h3>
            <span
              className={`inline-flex mt-1.5 items-center border px-1.5 py-0.5 mono text-[8px] sm:text-[9px] font-bold uppercase tracking-[0.14em] bg-white/80 ${variantBadge[variant]}`}
            >
              {badge}
            </span>
          </div>
          <div className="pt-0.5 text-right">
            {budiGapRm ? (
              <MarketGapChip gapRm={budiGapRm} />
            ) : change ? (
              <DeltaChip change={change} />
            ) : (
              <span className="mono text-[10px] text-[#a3a3a0]">—</span>
            )}
          </div>
        </header>

        <div className={`flex items-baseline gap-1 mono tabular-nums ${variantPrice[variant]}`}>
          <span className="text-[11px] sm:text-xs font-bold opacity-80">RM</span>
          <span className="serif text-[36px] sm:text-[48px] leading-none font-bold tracking-tight">
            {priceOk ? price : '—'}
          </span>
          {priceOk && (
            <span className="text-[11px] sm:text-xs font-semibold opacity-75 self-end mb-0.5 sm:mb-1">/L</span>
          )}
        </div>

        {prevPrice != null && (
          <p className="mono text-[10px] tracking-[0.08em] text-[#6b6b68]">
            PREV <span className="text-[#0a0a0a] tabular-nums">{prevPrice}</span>
          </p>
        )}
      </div>
    </article>
  );
}

/** RM/litre below RON95 market ceiling — top-right on BUDI95 card (ASCII hyphen for mobile font coverage). */
function MarketGapChip({ gapRm }: { gapRm: string }) {
  return (
    <span className="flex flex-col items-end gap-0.5 mono text-[#15803d]">
      <span className="whitespace-nowrap text-[10px] sm:text-[11px] font-bold tabular-nums leading-none">
        -RM {gapRm}
      </span>
      <span className="whitespace-nowrap text-[8px] sm:text-[9px] font-semibold uppercase tracking-[0.12em] text-[#6b6b68]">
        vs RON 95
      </span>
    </span>
  );
}

function DeltaChip({ change }: { change: NonNullable<PriceChange> }) {
  const isUp = change.direction === 'up';
  const isDown = change.direction === 'down';
  const color = isUp ? 'text-[#b91c1c]' : isDown ? 'text-[#15803d]' : 'text-[#6b6b68]';
  const sign = isUp ? '+' : isDown ? '−' : '±';
  const arrow = isUp ? '▲' : isDown ? '▼' : '■';
  return (
    <span className={`flex flex-col items-end gap-0.5 mono ${color}`}>
      <span className="inline-flex items-center gap-0.5 text-[10px] sm:text-[11px] font-bold tabular-nums">
        <span className="leading-none">{arrow}</span>
        {change.direction === 'flat' ? '0.0%' : `${change.pct}%`}
      </span>
      <span className="text-[9px] sm:text-[10px] tabular-nums opacity-90">
        {change.direction === 'flat' ? 'flat' : `${sign}RM ${change.amountRm}`}
      </span>
    </span>
  );
}
