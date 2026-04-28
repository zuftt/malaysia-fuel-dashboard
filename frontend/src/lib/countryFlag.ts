import { COUNTRY_FLAGS } from './constants';

export function countryFlag(code: string): string {
  return COUNTRY_FLAGS[code] || '🏳️';
}
