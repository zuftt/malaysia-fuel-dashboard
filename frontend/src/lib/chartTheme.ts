/** Aligns Recharts with design tokens (hex matches tailwind.config.js fuel-*). */
export const CHART_FONT = { xs: 10, sm: 11, base: 12 } as const;

export const FUEL_CHART_COLORS = {
  /** Matches RON95 card stripe / tailwind `fuel-ron95` (yellow-500). */
  ron95: '#eab308',
  ron97: '#388E3C',
  diesel: '#546E7A',
} as const;

export const ASEAN_BAR_COLORS = {
  subsidised: '#2E7D32',
  market: '#546E7A',
} as const;

export const CHART_TOOLTIP_STYLE = {
  borderRadius: 12,
  border: '1px solid #e2e8f0',
  fontSize: CHART_FONT.base,
} as const;
