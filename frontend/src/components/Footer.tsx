import { DATA_GOV_MY_FUEL_CATALOGUE, DATA_GOV_MY_FUEL_CSV } from '../lib/constants';

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="w-full border-t border-[#1a1a1a] bg-[#fafaf7] mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <p className="text-[12px] text-[#4b4b48] max-w-xl leading-relaxed">
          Independent feed. Peninsular levels from{' '}
          <a
            href={DATA_GOV_MY_FUEL_CATALOGUE}
            className="text-[#0a0a0a] underline decoration-[#1a1a1a] decoration-1 underline-offset-2 hover:decoration-[#c24300]"
            target="_blank"
            rel="noopener noreferrer"
          >
            data.gov.my
          </a>
          . Not affiliated with the Government of Malaysia.
        </p>
        <div className="flex flex-wrap gap-x-4 gap-y-2 mono text-[10px] tracking-[0.12em] uppercase">
          <a
            href={DATA_GOV_MY_FUEL_CSV}
            className="text-[#4b4b48] hover:text-[#0a0a0a]"
            target="_blank"
            rel="noopener noreferrer"
          >
            · CSV
          </a>
          <a
            href="https://github.com/zuftt/malaysia-fuel-dashboard"
            className="text-[#4b4b48] hover:text-[#0a0a0a]"
            target="_blank"
            rel="noopener noreferrer"
          >
            · GitHub
          </a>
          <span className="text-[#6b6b68]">© {year}</span>
        </div>
      </div>
    </footer>
  );
}
