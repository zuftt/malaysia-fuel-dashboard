import { Disclaimer } from './Disclaimer';
import { DATA_GOV_MY_FUEL_CATALOGUE } from '../lib/constants';

export function FaqSection() {
  return (
    <div className="panel p-5 sm:p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#e5e5e0]">
        <div className="pb-5 md:pb-0 md:pr-6">
          <p className="eyebrow mb-2">Q·01</p>
          <h3 className="serif text-lg font-semibold mb-2 text-[#0a0a0a]">How are pump prices set?</h3>
          <p className="text-[#4b4b48] text-[13px] leading-relaxed">
            The government sets retail ceilings through the{' '}
            <strong className="text-[#0a0a0a]">Automatic Pricing Mechanism (APM)</strong>. It reacts to crude
            benchmarks and the exchange rate. Official levels land on{' '}
            <a
              href={DATA_GOV_MY_FUEL_CATALOGUE}
              className="text-[#0a0a0a] underline decoration-[#1a1a1a] decoration-1 underline-offset-2 hover:decoration-[#c24300]"
              target="_blank"
              rel="noopener noreferrer"
            >
              data.gov.my
            </a>
            . For press statements use{' '}
            <a
              href="https://www.mof.gov.my/"
              className="text-[#0a0a0a] underline decoration-[#1a1a1a] decoration-1 underline-offset-2 hover:decoration-[#c24300]"
              target="_blank"
              rel="noopener noreferrer"
            >
              Ministry of Finance Malaysia
            </a>{' '}
            and{' '}
            <a
              href="https://www.kpdn.gov.my/"
              className="text-[#0a0a0a] underline decoration-[#1a1a1a] decoration-1 underline-offset-2 hover:decoration-[#c24300]"
              target="_blank"
              rel="noopener noreferrer"
            >
              KPDN
            </a>
            .
          </p>
        </div>
        <div className="pt-5 md:pt-0 md:pl-6">
          <p className="eyebrow mb-2">Q·02</p>
          <h3 className="serif text-lg font-semibold mb-2 text-[#0a0a0a]">Targeted subsidy</h3>
          <p className="text-[#4b4b48] text-[13px] leading-relaxed">
            RON 95 and diesel still carry policy support for eligible users. RON 97 tracks the market. Eligibility
            and programme rules sit with the Government, not with this dashboard.
          </p>
        </div>
      </div>

      <div className="mt-6">
        <Disclaimer title="What RONradar does not do" tone="neutral" icon="info">
          <ul className="text-[13px] leading-relaxed space-y-1 list-disc pl-5">
            <li>It does not predict future fuel prices.</li>
            <li>It does not give financial or investment advice.</li>
            <li>It does not verify BUDI95 or SPCS eligibility. Only MySubsidi and KPDN can do that.</li>
            <li>It does not store or sell what you type into calculators. Inputs stay in your browser.</li>
          </ul>
          <p className="mt-3 text-[13px]">
            Information here is for consumer understanding. For official policy, refer to Ministry of Finance and KPDN
            announcements.
          </p>
        </Disclaimer>
      </div>
    </div>
  );
}
