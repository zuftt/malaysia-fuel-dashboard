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

/**
 * Base list; BudiCalculator appends a dynamic "custom" row.
 * Specs sourced from Malaysian manufacturer sites (perodua.com.my, proton.com,
 * honda.com.my, toyota.com.my, nissan.com.my, yamaha-motor.com.my).
 * Consumption figures are manufacturer-claimed; real-world is typically 10–20% higher.
 */
export const POPULAR_CARS_BASE: PopularCar[] = [
  { id: 'myvi', name: 'Perodua Myvi 1.5', category: 'Hatchback', tank: 36, consumption: 5.4, quota: 200, years: '2017+ (Gen 3)' },
  { id: 'axia', name: 'Perodua Axia 1.0', category: 'Hatchback', tank: 36, consumption: 4.6, quota: 200, years: '2023+ (Gen 2)' },
  { id: 'bezza10', name: 'Perodua Bezza 1.0', category: 'Sedan', tank: 36, consumption: 4.6, quota: 200, years: '2016+' },
  { id: 'bezza15', name: 'Perodua Bezza 1.5', category: 'Sedan', tank: 36, consumption: 5.5, quota: 200, years: '2016+' },
  { id: 'ativa', name: 'Perodua Ativa 1.0T', category: 'SUV', tank: 36, consumption: 6.4, quota: 200, years: '2021+' },
  { id: 'aruz', name: 'Perodua Aruz 1.5', category: 'SUV', tank: 45, consumption: 6.7, quota: 200, years: '2019+' },
  { id: 'alza', name: 'Perodua Alza 1.5', category: 'MPV', tank: 36, consumption: 5.8, quota: 200, years: '2022+ (Gen 2)' },
  { id: 'saga', name: 'Proton Saga 1.3', category: 'Sedan', tank: 40, consumption: 5.6, quota: 200, years: '2016+' },
  { id: 'iriz', name: 'Proton Iriz 1.3', category: 'Hatchback', tank: 40, consumption: 5.7, quota: 200, years: '2014+' },
  { id: 'persona', name: 'Proton Persona 1.6', category: 'Sedan', tank: 45, consumption: 6.7, quota: 200, years: '2016+' },
  { id: 'x50', name: 'Proton X50 1.5T', category: 'SUV', tank: 47, consumption: 6.8, quota: 200, years: '2020+' },
  { id: 'x70', name: 'Proton X70 1.5T', category: 'SUV', tank: 55, consumption: 7.6, quota: 200, years: '2018+ (CKD 2020)' },
  { id: 'x90', name: 'Proton X90 1.5T', category: 'SUV 7-Seat', tank: 60, consumption: 8.4, quota: 200, years: '2023+' },
  { id: 'city', name: 'Honda City 1.5', category: 'Sedan', tank: 40, consumption: 5.6, quota: 200, years: '2020+ (Gen 7)' },
  { id: 'civic', name: 'Honda Civic 1.5T', category: 'Sedan', tank: 47, consumption: 6.7, quota: 200, years: '2022+ (Gen 11)' },
  { id: 'hrv', name: 'Honda HR-V 1.5T', category: 'SUV', tank: 40, consumption: 6.8, quota: 200, years: '2022+ (Gen 3)' },
  { id: 'crv', name: 'Honda CR-V 1.5T', category: 'SUV', tank: 57, consumption: 8.0, quota: 200, years: '2024+ (Gen 6)' },
  { id: 'vios', name: 'Toyota Vios 1.5', category: 'Sedan', tank: 40, consumption: 5.5, quota: 200, years: '2023+ (Gen 4)' },
  { id: 'yaris', name: 'Toyota Yaris 1.5', category: 'Hatchback', tank: 42, consumption: 5.6, quota: 200, years: '2019+' },
  { id: 'hilux', name: 'Toyota Hilux 2.4D', category: 'Pikap', tank: 80, consumption: 8.0, quota: 200, years: '2016+ (facelift 2024)' },
  { id: 'almera', name: 'Nissan Almera 1.0T', category: 'Sedan', tank: 41, consumption: 5.3, quota: 200, years: '2020+' },
];
