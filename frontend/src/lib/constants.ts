import type { PopularCar } from './types';

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/** Official pump price data (same as backend `data_fetcher`). */
export const DATA_GOV_MY_FUEL_CSV = 'https://storage.data.gov.my/commodities/fuelprice.csv';
export const DATA_GOV_MY_FUEL_CATALOGUE = 'https://data.gov.my/data-catalogue/fuelprice';

export const COUNTRY_FLAGS: Record<string, string> = {
  MY: '🇲🇾',
  SG: '🇸🇬',
  TH: '🇹🇭',
  ID: '🇮🇩',
  BN: '🇧🇳',
  PH: '🇵🇭',
};

/** Base list; BudiCalculator appends a dynamic "custom" row. */
export const POPULAR_CARS_BASE: PopularCar[] = [
  { id: 'myvi', name: 'Perodua Myvi 1.5', category: 'Hatchback', tank: 36, consumption: 5.8, quota: 200 },
  { id: 'axia', name: 'Perodua Axia / Bezza 1.0', category: 'Hatchback / Sedan', tank: 36, consumption: 5.1, quota: 200 },
  { id: 'bezza15', name: 'Perodua Bezza 1.5', category: 'Sedan', tank: 36, consumption: 5.5, quota: 200 },
  { id: 'ativa', name: 'Perodua Ativa 1.0T', category: 'SUV', tank: 36, consumption: 6.3, quota: 200 },
  { id: 'aruz', name: 'Perodua Aruz 1.5', category: 'SUV', tank: 43, consumption: 7.5, quota: 200 },
  { id: 'alza', name: 'Perodua Alza 1.5', category: 'MPV', tank: 42, consumption: 6.5, quota: 200 },
  { id: 'saga', name: 'Proton Saga 1.3', category: 'Sedan', tank: 40, consumption: 6.2, quota: 200 },
  { id: 'iriz', name: 'Proton Iriz 1.3', category: 'Hatchback', tank: 40, consumption: 5.8, quota: 200 },
  { id: 'persona', name: 'Proton Persona 1.6', category: 'Sedan', tank: 45, consumption: 6.8, quota: 200 },
  { id: 'x50', name: 'Proton X50 1.5T', category: 'SUV', tank: 48, consumption: 7.0, quota: 200 },
  { id: 'x70', name: 'Proton X70 1.5T', category: 'SUV', tank: 51, consumption: 7.8, quota: 200 },
  { id: 'x90', name: 'Proton X90 1.5T', category: 'SUV 7-Seat', tank: 52, consumption: 8.5, quota: 200 },
  { id: 'city', name: 'Honda City 1.5', category: 'Sedan', tank: 40, consumption: 5.7, quota: 200 },
  { id: 'civic', name: 'Honda Civic 1.5T', category: 'Sedan', tank: 47, consumption: 6.7, quota: 200 },
  { id: 'hrv', name: 'Honda HR-V 1.5T', category: 'SUV', tank: 40, consumption: 6.8, quota: 200 },
  { id: 'crv', name: 'Honda CR-V 1.5T', category: 'SUV', tank: 53, consumption: 8.0, quota: 200 },
  { id: 'vios', name: 'Toyota Vios 1.5', category: 'Sedan', tank: 42, consumption: 5.9, quota: 200 },
  { id: 'yaris', name: 'Toyota Yaris / Vios 1.5', category: 'Hatchback', tank: 42, consumption: 5.6, quota: 200 },
  { id: 'hilux', name: 'Toyota Hilux 2.4D', category: 'Pikap', tank: 80, consumption: 9.5, quota: 200 },
  { id: 'almera', name: 'Nissan Almera 1.0T', category: 'Sedan', tank: 41, consumption: 5.3, quota: 200 },
  { id: 'y15', name: 'Yamaha Y15ZR / LC135', category: 'Motosikal Kapcai', tank: 4.2, consumption: 2.0, quota: 100 },
  { id: 'rs150', name: 'Honda RS150R / Wave', category: 'Motosikal Kapcai', tank: 4.6, consumption: 2.2, quota: 100 },
  { id: 'nmax', name: 'Yamaha NMax 155', category: 'Motosikal Skuter', tank: 7.1, consumption: 2.8, quota: 100 },
];
