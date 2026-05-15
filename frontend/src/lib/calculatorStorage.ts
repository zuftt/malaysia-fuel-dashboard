/**
 * Persisted calculator inputs, shared between `/` (BudiCalculator) and
 * `/console` (QuotaTicker). Stored in localStorage so opening the console
 * shows the same vehicle/distance the user already configured.
 */

const STORAGE_KEY = 'rr_calc_state_v1';

export interface CalculatorState {
  carModel: string;
  kmDay: number;
  tankSize: number;
  consumption: number;
}

export const CALCULATOR_DEFAULTS: CalculatorState = {
  carModel: 'myvi',
  kmDay: 40,
  tankSize: 45,
  consumption: 8.5,
};

export function readCalculatorState(): CalculatorState {
  if (typeof window === 'undefined') return CALCULATOR_DEFAULTS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return CALCULATOR_DEFAULTS;
    const parsed = JSON.parse(raw) as Partial<CalculatorState>;
    return {
      carModel: typeof parsed.carModel === 'string' ? parsed.carModel : CALCULATOR_DEFAULTS.carModel,
      kmDay: Number.isFinite(parsed.kmDay) ? Number(parsed.kmDay) : CALCULATOR_DEFAULTS.kmDay,
      tankSize: Number.isFinite(parsed.tankSize) ? Number(parsed.tankSize) : CALCULATOR_DEFAULTS.tankSize,
      consumption: Number.isFinite(parsed.consumption)
        ? Number(parsed.consumption)
        : CALCULATOR_DEFAULTS.consumption,
    };
  } catch {
    return CALCULATOR_DEFAULTS;
  }
}

export function writeCalculatorState(state: CalculatorState): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // localStorage full or unavailable — silently skip.
  }
}
