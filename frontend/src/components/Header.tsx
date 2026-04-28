import { Icon } from './Icon';

const NAV_LINKS = [
  { href: '#prices', label: 'Prices', mobileLabel: 'Prices', icon: 'local_gas_station' },
  { href: '#asean', label: 'ASEAN', mobileLabel: 'ASEAN', icon: 'public' },
  { href: '#trend', label: 'Trend', mobileLabel: 'Trend', icon: 'trending_up' },
  { href: '#calculator', label: 'Calculator', mobileLabel: 'Calc', icon: 'calculate' },
  { href: '#news', label: 'News', mobileLabel: 'News', icon: 'newspaper' },
];

export function Header() {
  return (
    <>
      <header className="fixed top-0 w-full z-50 border-b border-[#1a1a1a] bg-[#fafaf7] rr-header-in">
        <div className="flex justify-between items-stretch px-4 sm:px-6 max-w-7xl mx-auto gap-4 h-12">
          <a href="#top" className="flex items-center gap-2 shrink-0">
            <Icon name="radar" className="text-[#0a0a0a] text-[20px]" />
            <span className="mono text-[13px] font-bold text-[#0a0a0a] tracking-[0.12em]">RONRADAR</span>
            <span className="hidden sm:inline mono text-[10px] text-[#6b6b68] tracking-[0.18em]">/ MY · FUEL</span>
          </a>
          <nav className="hidden sm:flex items-stretch text-[11px] mono font-semibold tracking-[0.12em] uppercase">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="flex items-center px-3 border-l border-[#e5e5e0] text-[#4b4b48] hover:text-[#0a0a0a] hover:bg-[#f1f1ec] transition-colors"
              >
                {link.label}
              </a>
            ))}
          </nav>
        </div>
      </header>

      <nav
        aria-label="Mobile navigation"
        className="sm:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#fafaf7] border-t border-[#1a1a1a]"
      >
        <ul className="grid grid-cols-5">
          {NAV_LINKS.map((link) => (
            <li key={link.href} className="border-r last:border-r-0 border-[#e5e5e0]">
              <a
                href={link.href}
                className="flex flex-col items-center justify-center gap-1 py-2 mono text-[10px] font-semibold tracking-[0.08em] uppercase text-[#4b4b48] active:bg-[#f1f1ec] active:text-[#0a0a0a]"
                style={{ minHeight: 56 }}
              >
                <Icon name={link.icon} className="text-[18px] text-[#0a0a0a]" />
                <span>{link.mobileLabel}</span>
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </>
  );
}
