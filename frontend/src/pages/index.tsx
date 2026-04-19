import { useState, useEffect } from 'react';
import Head from 'next/head';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const formatPrice = (value: any): string => {
  if (value === null || value === undefined) return '--';
  const num = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(num)) return '--';
  return num.toFixed(2);
};

interface FuelPrice {
  date_announced: string;
  ron95_subsidized: number;
  ron95_market: number;
  ron97: number;
  diesel_peninsular: number;
}

interface TrendData {
  date: string;
  fuel_type?: string;
  local_price: number;
  global_reference: number;
  subsidy_gap: number;
}

interface NewsArticle {
  id: number;
  title: string;
  source: string;
  source_url: string | null;
  announcement_date: string;
  announcement_type: string;
  content?: string | null;
}

function formatRelativeMs(iso: string): string {
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

function shortSourceLabel(source: string): string {
  if (source.startsWith('RSS · ')) return source.slice(6);
  return source;
}

function Icon({ name, className = '', fill = false }: { name: string; className?: string; fill?: boolean }) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      style={fill ? { fontVariationSettings: "'FILL' 1" } : undefined}
    >
      {name}
    </span>
  );
}

export default function Home() {
  const [prices, setPrices] = useState<FuelPrice | null>(null);
  const [prevPrices, setPrevPrices] = useState<FuelPrice | null>(null);
  const [trends, setTrends] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'weekly' | 'monthly'>('weekly');
  const [chartFilter, setChartFilter] = useState<'all' | 'ron97' | 'diesel'>('all');
  const [articles, setArticles] = useState<NewsArticle[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [priceRes, trendRes, newsRes] = await Promise.all([
          axios.get(`${API_URL}/api/v1/prices/latest`),
          axios.get(`${API_URL}/api/v1/prices/history?days=84`),
          axios.get(`${API_URL}/api/v1/news/latest?limit=9`).catch(() => ({ data: { data: [] as NewsArticle[] } })),
        ]);

        setPrices(priceRes.data?.data ?? priceRes.data);

        const trendData = trendRes.data?.data ?? trendRes.data ?? [];
        setTrends(trendData);

        const newsRows = newsRes.data?.data ?? [];
        setArticles(Array.isArray(newsRows) ? newsRows : []);

        // Derive previous week's prices from history for change calculation
        if (trendData.length >= 2) {
          const dates = [...new Set(trendData.map((t: TrendData) => t.date))].sort().reverse();
          if (dates.length >= 2) {
            const prevDate = dates[1];
            const prevWeek = trendData.filter((t: TrendData) => t.date === prevDate);
            const prevRon97 = prevWeek.find((t: TrendData) => t.fuel_type === 'RON97');
            const prevDiesel = prevWeek.find((t: TrendData) => t.fuel_type === 'Diesel');
            const prevRon95 = prevWeek.find((t: TrendData) => t.fuel_type === 'RON95');
            setPrevPrices({
              date_announced: String(prevDate),
              ron95_subsidized: prevRon95?.local_price ?? 0,
              ron95_market: 0,
              ron97: prevRon97?.local_price ?? 0,
              diesel_peninsular: prevDiesel?.local_price ?? 0,
            });
          }
        }

        setError(null);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Gagal memuatkan data. Pastikan API sedang berjalan.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-on-surface-variant font-body">Memuatkan harga minyak...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="bg-surface-container-lowest p-8 rounded-lg max-w-md">
          <h2 className="text-2xl font-bold text-error mb-4 font-headline">Ralat</h2>
          <p className="text-on-surface mb-4 font-body">{error}</p>
          <p className="text-sm text-on-surface-variant font-body">API URL: {API_URL}</p>
        </div>
      </div>
    );
  }

  // Compute actual week-over-week price changes from data
  const getChange = (current: number | undefined, previous: number | undefined) => {
    if (!current || !previous || current === previous) return null;
    const diff = Number(current) - Number(previous);
    return {
      direction: diff > 0 ? ('up' as const) : ('down' as const),
      amount: Math.abs(diff).toFixed(2),
    };
  };

  const fuelCards = [
    {
      name: 'RON 95',
      price: formatPrice(prices?.ron95_market),
      badge: 'Pasaran',
      change: getChange(prices?.ron95_market, prevPrices?.ron95_market),
      note: 'Harga pasaran RON 95 tanpa subsidi.',
      bg: '#FFF8E1',
      accent: '#F9A825',
    },
    {
      name: 'RON 95 Budi',
      price: formatPrice(prices?.ron95_subsidized),
      badge: 'Subsidi',
      change: getChange(prices?.ron95_subsidized, prevPrices?.ron95_subsidized),
      note: 'Harga khusus untuk penerima bantuan Budi Madani.',
      bg: '#E3F2FD',
      accent: '#1976D2',
    },
    {
      name: 'RON 97',
      price: formatPrice(prices?.ron97),
      badge: 'Pasaran',
      change: getChange(prices?.ron97, prevPrices?.ron97),
      note: 'Harga apungan mengikut harga pasaran dunia.',
      bg: '#E8F5E9',
      accent: '#388E3C',
    },
    {
      name: 'Diesel',
      price: formatPrice(prices?.diesel_peninsular),
      badge: 'Pasaran',
      change: getChange(prices?.diesel_peninsular, prevPrices?.diesel_peninsular),
      note: 'Harga runcit diesel di Semenanjung Malaysia.',
      bg: '#ECEFF1',
      accent: '#37474F',
    },
  ];

  return (
    <>
      <Head>
        <title>Harga Minyak Mingguan | Malaysia</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </Head>

      <div className="bg-surface text-on-surface min-h-screen flex flex-col">
        {/* Header */}
        <header className="fixed top-0 w-full z-50 bg-white/70 backdrop-blur-xl shadow-sm">
          <div className="flex justify-between items-center px-6 py-4 max-w-7xl mx-auto">
            <div className="flex items-center gap-8">
              <span className="text-2xl font-black text-slate-800 tracking-tight font-headline">
                Harga Minyak Mingguan
              </span>
              <nav className="hidden md:flex items-center gap-6">
                <button
                  onClick={() => setActiveTab('weekly')}
                  className={`font-headline pb-1 transition-colors ${
                    activeTab === 'weekly'
                      ? 'text-blue-600 border-b-2 border-blue-600 font-bold'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  Mingguan
                </button>
                <button
                  onClick={() => setActiveTab('monthly')}
                  className={`font-headline pb-1 transition-colors ${
                    activeTab === 'monthly'
                      ? 'text-blue-600 border-b-2 border-blue-600 font-bold'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  Bulanan
                </button>
              </nav>
            </div>
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center bg-slate-100/50 rounded-full px-4 py-2 gap-2">
                <Icon name="search" className="text-slate-500 text-sm" />
                <input
                  className="bg-transparent border-none focus:ring-0 focus:outline-none text-sm w-32 md:w-48"
                  placeholder="Cari harga..."
                  type="text"
                />
              </div>
              <button className="hover:bg-slate-100/50 p-2 rounded-full transition-all active:scale-95">
                <Icon name="notifications" />
              </button>
            </div>
          </div>
        </header>

        <main className="mt-24 px-6 max-w-7xl mx-auto w-full flex-grow pb-32">
          {/* Hero Header */}
          <section className="mb-12">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div>
                <h1 className="text-4xl font-extrabold font-headline tracking-tight text-on-background mb-2">
                  {prices?.date_announced
                    ? new Date(prices.date_announced).toLocaleDateString('ms-MY', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })
                    : '—'}
                </h1>
                <div className="inline-flex items-center bg-surface-container-high rounded-full px-4 py-1.5 gap-2">
                  <span className="w-2 h-2 rounded-full bg-secondary animate-pulse"></span>
                  <span className="text-sm font-medium text-on-surface-variant">
                    Dikemaskini setiap petang Rabu
                  </span>
                </div>
              </div>
              <div className="flex bg-surface-container rounded-full p-1 self-start">
                <button
                  onClick={() => setActiveTab('weekly')}
                  className={`px-6 py-2 rounded-full text-sm font-bold transition-all ${
                    activeTab === 'weekly'
                      ? 'bg-surface-container-lowest shadow-sm text-primary'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Mingguan
                </button>
                <button
                  onClick={() => setActiveTab('monthly')}
                  className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
                    activeTab === 'monthly'
                      ? 'bg-surface-container-lowest shadow-sm text-primary'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Bulanan
                </button>
              </div>
            </div>
          </section>

          {/* Fuel Price Cards */}
          <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {fuelCards.map((card) => (
              <div
                key={card.name}
                className="rounded-lg p-8 transition-transform hover:scale-[1.02] duration-300"
                style={{ backgroundColor: card.bg }}
              >
                <div className="flex justify-between items-start mb-8">
                  <div>
                    <h3
                      className="text-xl font-bold font-headline"
                      style={{ color: card.accent }}
                    >
                      {card.name}
                    </h3>
                    <span
                      className="inline-block mt-2 px-3 py-1 bg-white/50 rounded-full text-[10px] font-bold uppercase tracking-wider"
                      style={{ color: card.accent }}
                    >
                      {card.badge}
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    {card.change ? (
                      <span
                        className={`flex items-center gap-0.5 text-xs font-bold ${
                          card.change.direction === 'up' ? 'text-error' : 'text-secondary'
                        }`}
                      >
                        <Icon
                          name={card.change.direction === 'up' ? 'arrow_upward' : 'arrow_downward'}
                          className="text-sm"
                        />
                        RM {card.change.amount}
                      </span>
                    ) : (
                      <span className="text-xs font-medium text-on-surface-variant opacity-60">
                        RM 0.00
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-baseline gap-1">
                  <span
                    className="text-lg font-bold font-headline"
                    style={{ color: card.accent, opacity: 0.8 }}
                  >
                    RM
                  </span>
                  <span
                    className="text-5xl font-black font-headline tracking-tighter"
                    style={{ color: card.accent }}
                  >
                    {card.price}
                  </span>
                </div>
                <div
                  className="mt-6 pt-6"
                  style={{ borderTop: `1px solid ${card.accent}15` }}
                >
                  <p
                    className="text-xs leading-relaxed font-medium"
                    style={{ color: card.accent, opacity: 0.7 }}
                  >
                    {card.note}
                  </p>
                </div>
              </div>
            ))}
          </section>

          {/* Chart Section */}
          <section className="bg-surface-container-low rounded-lg p-8 border border-white/40 shadow-sm relative overflow-hidden mb-16">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-10">
              <div>
                <h2 className="text-2xl font-bold font-headline mb-1">Trend Harga 12 Minggu</h2>
                <p className="text-on-surface-variant text-sm">
                  Prestasi harga RON 97 & Diesel berbanding penanda aras subsidi.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {(['all', 'ron97', 'diesel'] as const).map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setChartFilter(filter)}
                    className={`px-4 py-2 rounded-full text-xs font-bold transition-colors ${
                      chartFilter === filter
                        ? 'bg-primary text-on-primary shadow-md'
                        : 'bg-surface-container-highest text-on-surface-variant hover:bg-surface-container-high'
                    }`}
                  >
                    {filter === 'all' ? 'Semua' : filter === 'ron97' ? 'RON 97' : 'Diesel'}
                  </button>
                ))}
              </div>
            </div>

            {trends.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={trends}>
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: '#595c5d' }}
                    tickLine={false}
                    axisLine={false}
                    interval={Math.max(0, Math.floor(trends.length / 5) - 1)}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: '#595c5d' }}
                    tickLine={false}
                    axisLine={false}
                    domain={['auto', 'auto']}
                  />
                  <Tooltip
                    formatter={(value: any) => `RM ${formatPrice(value)}`}
                    labelFormatter={(label) => label}
                    contentStyle={{
                      background: 'rgba(255,255,255,0.9)',
                      backdropFilter: 'blur(20px)',
                      border: '1px solid rgba(255,255,255,0.5)',
                      borderRadius: '12px',
                      fontSize: '12px',
                      boxShadow: '0 8px 40px rgba(44,47,48,0.06)',
                    }}
                  />
                  {(chartFilter === 'all' || chartFilter === 'ron97') && (
                    <Line
                      type="monotone"
                      dataKey="local_price"
                      stroke="#388E3C"
                      name="RON 97"
                      strokeWidth={3}
                      dot={false}
                      strokeLinecap="round"
                    />
                  )}
                  {(chartFilter === 'all' || chartFilter === 'diesel') && (
                    <Line
                      type="monotone"
                      dataKey="global_reference"
                      stroke="#37474F"
                      name="Diesel"
                      strokeWidth={3}
                      dot={false}
                      strokeLinecap="round"
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-80 flex items-center justify-center">
                <p className="text-on-surface-variant">Tiada data sejarah tersedia</p>
              </div>
            )}

            <div className="mt-6 flex justify-between text-[10px] font-bold text-on-surface-variant uppercase tracking-widest px-2">
              <span>Januari</span>
              <span>Februari</span>
              <span>Mac</span>
              <span>April</span>
            </div>
          </section>

          {/* News Section */}
          <section className="mb-16">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <Icon name="feed" className="text-[#1976D2]" />
                <h2 className="text-2xl font-extrabold font-headline tracking-tight">
                  Berita Terkini
                </h2>
              </div>
              <a
                href="https://news.google.com/search?q=Malaysia+petrol+RON+subsidi+minyak&hl=en-MY&gl=MY&ceid=MY:en"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary text-sm font-bold font-headline hover:bg-primary/5 px-3 py-1.5 rounded-full transition-colors flex items-center gap-0.5"
              >
                <span>Lagi Berita</span>
                <Icon name="chevron_right" className="text-[18px]" />
              </a>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
              {articles.length === 0 ? (
                <div className="col-span-full rounded-2xl border border-slate-200 bg-slate-50/80 px-6 py-10 text-center text-on-surface-variant">
                  <p className="font-body text-sm mb-2">
                    Tiada berita ditapis buat masa ini — atau API masih menyegerakkan RSS.
                  </p>
                  <p className="text-xs opacity-80">
                    Pastikan backend boleh akses internet untuk Google News RSS (semak firewall).
                  </p>
                </div>
              ) : (
                articles.map((article, i) => {
                  const hue = [210, 145, 175][i % 3];
                  const tag =
                    article.announcement_type === 'News Feed'
                      ? 'Berita langsung'
                      : article.announcement_type;
                  const tagStyle =
                    article.announcement_type === 'News Feed'
                      ? 'text-primary bg-primary/10'
                      : 'text-slate-500 bg-slate-100';
                  const href = article.source_url || '#';
                  const CardInner = (
                    <>
                      <div
                        className="aspect-[16/9] w-full rounded-2xl overflow-hidden mb-4 flex items-center justify-center text-white/90 text-sm font-bold tracking-wide"
                        style={{
                          background: `linear-gradient(135deg, hsl(${hue}, 55%, 42%) 0%, hsl(${hue}, 35%, 28%) 100%)`,
                        }}
                      >
                        <Icon name="article" className="text-5xl opacity-90" />
                      </div>
                      <div className="flex-1 px-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span
                            className={`text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded ${tagStyle}`}
                          >
                            {tag}
                          </span>
                        </div>
                        <h3 className="font-headline font-bold text-lg text-on-surface leading-tight mb-2 group-hover:text-primary transition-colors">
                          {article.title}
                        </h3>
                        <p className="text-xs text-on-surface-variant line-clamp-2 mb-3 opacity-85">
                          {(article.content || '').replace(/\s+/g, ' ').slice(0, 160)}
                          {(article.content || '').length > 160 ? '…' : ''}
                        </p>
                        <div className="flex items-center gap-1.5 text-on-surface-variant text-xs opacity-70">
                          <span>{shortSourceLabel(article.source)}</span>
                          <span className="w-0.5 h-0.5 rounded-full bg-current"></span>
                          <span>{formatRelativeMs(article.announcement_date)}</span>
                        </div>
                      </div>
                    </>
                  );
                  return article.source_url ? (
                    <a
                      key={article.id}
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex flex-col bg-white rounded-2xl overflow-hidden hover:bg-slate-50/80 transition-colors cursor-pointer group text-left no-underline"
                    >
                      {CardInner}
                    </a>
                  ) : (
                    <div
                      key={article.id}
                      className="flex flex-col bg-white rounded-2xl overflow-hidden hover:bg-slate-50/80 transition-colors group"
                    >
                      {CardInner}
                    </div>
                  );
                })
              )}
            </div>
          </section>

          {/* FAQ Section */}
          <section className="mb-16 bg-[#F8F9FA] rounded-lg p-8 md:p-12 border border-slate-200/60 shadow-sm">
            <div className="flex items-center gap-3 mb-10">
              <Icon name="info" className="text-primary text-3xl" />
              <h2 className="text-3xl font-extrabold font-headline tracking-tight text-on-background">
                Apa Yang Anda Perlu Tahu
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
              <div className="flex flex-col gap-4">
                <div className="w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center border border-slate-100">
                  <Icon name="analytics" className="text-primary" />
                </div>
                <div>
                  <h3 className="font-headline font-bold text-lg mb-3 text-on-background">
                    Bagaimana Harga Ditentukan?
                  </h3>
                  <p className="text-on-surface-variant text-sm leading-relaxed">
                    Harga runcit ditentukan melalui <strong>Mekanisme Harga Automatik (APM)</strong>.
                    Ia dipengaruhi oleh harga minyak mentah dunia (Brent/WTI) dan kadar pertukaran
                    mata wang asing. Kerajaan menyelaraskan harga setiap minggu untuk menstabilkan
                    kesan ekonomi kepada rakyat.
                  </p>
                </div>
              </div>
              <div className="flex flex-col gap-4">
                <div className="w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center border border-slate-100">
                  <Icon name="account_balance_wallet" className="text-secondary" />
                </div>
                <div>
                  <h3 className="font-headline font-bold text-lg mb-3 text-on-background">
                    Subsidi Bersasar
                  </h3>
                  <p className="text-on-surface-variant text-sm leading-relaxed">
                    Produk seperti{' '}
                    <span className="border-b-2 border-[#F9A825]/30 font-medium">RON 95</span> dan{' '}
                    <span className="border-b-2 border-[#37474F]/30 font-medium">Diesel</span>{' '}
                    menerima subsidi kerajaan untuk mengekalkan harga rendah bagi golongan layak.
                    Manakala{' '}
                    <span className="border-b-2 border-[#388E3C]/30 font-medium">RON 97</span>{' '}
                    dijual pada harga apungan pasaran tanpa subsidi.
                  </p>
                </div>
              </div>
              <div className="flex flex-col gap-4">
                <div className="w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center border border-slate-100">
                  <Icon name="lightbulb" className="text-tertiary" />
                </div>
                <div>
                  <h3 className="font-headline font-bold text-lg mb-3 text-on-background">
                    Tips Pengguna
                  </h3>
                  <ul className="text-on-surface-variant text-sm leading-relaxed space-y-2">
                    <li className="flex items-start gap-2">
                      <span className="text-primary mt-1">•</span>
                      <span>
                        Pastikan tekanan tayar mengikut spesifikasi untuk penjimatan bahan api
                        sehingga 3%.
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-primary mt-1">•</span>
                      <span>
                        Gunakan gred bahan api (RON 95/97) yang disyorkan oleh pengeluar kenderaan
                        anda.
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-primary mt-1">•</span>
                      <span>
                        Elakkan pecutan drastik; memandu secara konsisten membantu kecekapan enjin.
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* Subsidy Check CTA */}
          <section className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-8 items-center bg-primary rounded-lg overflow-hidden shadow-2xl">
            <div className="p-12 text-on-primary">
              <h2 className="text-3xl font-black font-headline mb-4 leading-tight">
                Adakah anda layak untuk subsidi Budi Madani?
              </h2>
              <p className="mb-8 opacity-90 text-sm leading-relaxed max-w-md">
                Semak kelayakan anda untuk mendapatkan harga RON 95 pada RM 2.05 se-liter melalui
                inisiatif penyasaran subsidi Kerajaan Malaysia.
              </p>
              <div className="flex flex-wrap gap-4">
                <button className="bg-surface-container-lowest text-primary font-black px-8 py-4 rounded-full hover:scale-105 transition-transform">
                  Semak Kelayakan
                </button>
                <button className="border-2 border-white/30 text-white font-bold px-8 py-4 rounded-full hover:bg-white/10 transition-colors">
                  Ketahui Lanjut
                </button>
              </div>
            </div>
            <div className="relative h-full min-h-[300px] hidden md:flex items-center justify-center bg-primary-container/20">
              <Icon name="verified" className="text-[120px] text-white/20" />
            </div>
          </section>
        </main>

        {/* Footer */}
        <footer className="w-full py-12 px-6 mt-auto bg-slate-50 border-t border-slate-200/50">
          <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="text-center md:text-left">
              <span className="font-bold text-slate-400 block mb-2 font-headline uppercase tracking-tighter">
                Harga Minyak Malaysia
              </span>
              <p className="font-body text-xs leading-relaxed text-slate-500">
                Maklumat adalah berdasarkan data terbuka kerajaan. Harga ditetapkan oleh Kementerian
                Kewangan setiap petang Rabu.
              </p>
            </div>
            <nav className="flex gap-6">
              <a
                href="#"
                className="text-slate-500 hover:text-slate-900 transition-colors text-xs font-bold uppercase tracking-wider"
              >
                Dasar Privasi
              </a>
              <a
                href="#"
                className="text-slate-500 hover:text-slate-900 transition-colors text-xs font-bold uppercase tracking-wider"
              >
                Terma Penggunaan
              </a>
              <a
                href="#"
                className="text-slate-500 hover:text-slate-900 transition-colors text-xs font-bold uppercase tracking-wider"
              >
                Hubungi Kami
              </a>
            </nav>
          </div>
        </footer>

        {/* Mobile Bottom Nav */}
        <nav className="fixed bottom-0 left-0 w-full flex justify-around items-center px-4 pb-6 pt-3 bg-white/70 backdrop-blur-xl border-t border-slate-100 md:hidden z-50">
          <button className="flex flex-col items-center justify-center bg-blue-50 text-blue-700 rounded-full px-6 py-2 scale-105 transition-transform">
            <Icon name="equalizer" fill />
            <span className="text-[10px] font-medium font-headline">Harga</span>
          </button>
          <button className="flex flex-col items-center justify-center text-slate-400 px-4 py-2 hover:text-blue-500 transition-colors">
            <Icon name="show_chart" />
            <span className="text-[10px] font-medium font-headline">Graf</span>
          </button>
          <button className="flex flex-col items-center justify-center text-slate-400 px-4 py-2 hover:text-blue-500 transition-colors">
            <Icon name="verified" />
            <span className="text-[10px] font-medium font-headline">Kelayakan</span>
          </button>
          <button className="flex flex-col items-center justify-center text-slate-400 px-4 py-2 hover:text-blue-500 transition-colors">
            <Icon name="person" />
            <span className="text-[10px] font-medium font-headline">Profil</span>
          </button>
        </nav>
      </div>
    </>
  );
}
