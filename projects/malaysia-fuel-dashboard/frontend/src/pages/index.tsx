import { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FuelPrice {
  date_announced: string;
  ron95_subsidized: number;
  ron97: number;
  diesel_peninsular: number;
}

interface TrendData {
  date: string;
  local_price: number;
  global_reference: number;
  subsidy_gap: number;
}

export default function Home() {
  const [prices, setPrices] = useState<FuelPrice | null>(null);
  const [trends, setTrends] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch latest prices
        const priceRes = await axios.get(`${API_URL}/api/v1/prices/latest`);
        setPrices(priceRes.data.data);

        // Fetch trend data
        const trendRes = await axios.get(`${API_URL}/api/v1/prices/history?days=30`);
        setTrends(trendRes.data.data);

        setError(null);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to fetch data. Make sure the API is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading fuel prices...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md">
          <h2 className="text-2xl font-bold text-red-600 mb-4">⚠️ Error</h2>
          <p className="text-gray-700 mb-4">{error}</p>
          <p className="text-sm text-gray-500">API URL: {API_URL}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900">🇲🇾 Fuel Intelligence</h1>
              <p className="text-gray-600 mt-2">Real-time fuel price monitoring for Malaysia</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Last updated: {new Date().toLocaleTimeString()}</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Price Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* RON95 */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">RON95 (Subsidized)</p>
                <p className="text-4xl font-bold text-blue-600 mt-2">
                  RM {prices?.ron95_subsidized?.toFixed(2) || '--'}
                </p>
              </div>
              <div className="text-5xl">⛽</div>
            </div>
            <p className="text-xs text-gray-500 mt-4">Petrol (Regular)</p>
          </div>

          {/* RON97 */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">RON97</p>
                <p className="text-4xl font-bold text-amber-600 mt-2">
                  RM {prices?.ron97?.toFixed(2) || '--'}
                </p>
              </div>
              <div className="text-5xl">🔥</div>
            </div>
            <p className="text-xs text-gray-500 mt-4">Premium Petrol</p>
          </div>

          {/* Diesel */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Diesel</p>
                <p className="text-4xl font-bold text-emerald-600 mt-2">
                  RM {prices?.diesel_peninsular?.toFixed(2) || '--'}
                </p>
              </div>
              <div className="text-5xl">🚗</div>
            </div>
            <p className="text-xs text-gray-500 mt-4">Diesel (Peninsular)</p>
          </div>
        </div>

        {/* Charts */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">30-Day Price Trend</h2>
          
          {trends.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  interval={Math.floor(trends.length / 7)}
                />
                <YAxis />
                <Tooltip 
                  formatter={(value: any) => value?.toFixed(2)}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="local_price" 
                  stroke="#3b82f6" 
                  name="Malaysia Price"
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="global_reference" 
                  stroke="#ef4444" 
                  name="Global Reference (MOPS)"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500">No historical data available</p>
          )}
        </div>

        {/* Subsidy Gap */}
        {trends.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Subsidy Gap Analysis</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trends.slice(-7)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip formatter={(value: any) => value?.toFixed(2)} />
                <Legend />
                <Bar 
                  dataKey="subsidy_gap" 
                  fill="#8b5cf6" 
                  name="Subsidy Gap (RM)"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
            <p className="text-sm text-gray-600 mt-4">
              The gap between Malaysia's subsidized price and global market prices.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-400">
            Built with ❤️ for Malaysia's fuel intelligence community
          </p>
          <p className="text-sm text-gray-500 mt-2">
            API: {API_URL}
          </p>
        </div>
      </footer>
    </div>
  );
}
