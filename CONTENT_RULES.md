# Content and copy rules (RONradar)

Use this document for all user-facing copy, disclaimers, and data labelling. Cursor and contributors should follow it when editing the site.

## 1. Tone and voice

- Explain fuel prices like you would to a friend who is smart but not a finance expert. Be clear, direct, and conversational.
- No corporate fluff. Avoid phrases like "we are committed to", "empowering consumers", and "leveraging data". Say what the thing does.
- No hype. Do not call anything "revolutionary", "game-changing", or "the only tool you need".
- Prefer short sentences. One idea per sentence where possible.
- Use active voice. Example: "The government sets the price weekly" not "prices are set weekly by the government".
- Use British and Malaysian English spelling (litre, subsidised, programme), not American.
- Do not use em-dashes or Oxford commas as list separators. Use full stops, "and", or bullet points.

## 2. Factual accuracy

- Every official pump price must show its **source** and **last retrieved** timestamp. No exceptions.
- Never invent or approximate an official price. If data is missing or the client cannot reach the API, show **Data temporarily unavailable** instead of a guessed number.
- When subsidy rules, eligibility, or policy are cited, link to a **primary** source (for example [data.gov.my](https://data.gov.my/data-catalogue/fuelprice), Ministry of Finance Malaysia, KPDN, or the official BUDI95 or MySubsidi programme page).
- If a source changes schema or URL, the UI must fail safely with **Data temporarily unavailable** rather than a stale or guessed figure.
- Historical weekly prices must match data.gov.my. Do not round beyond the source, smooth series, or interpolate missing weeks.

## 3. Estimates versus facts

- Pump prices from data.gov.my need no "estimate" label. They are facts.
- Anything calculated (monthly cost, quota duration, regional USD or MYR equivalents, savings) must be labelled as an **estimate** with a consistent marker (for example a small **Estimate** pill or italic caveat under the figure).
- Never show an estimate without stating the **assumptions**: inputs and the logic in plain language (for example "litres per month = (km per month ÷ 100) × litres per 100 km").
- Currency-converted comparison values must show the **FX rate** and **date** used (for example "USD 0.61/litre at MYR 4.2800/USD, 16 Apr 2026").

## 4. Disclaimers (short, placed where they matter)

- **Footer (persistent):** RONradar is independent. Prices come from data.gov.my (Ministry of Finance). This site is not affiliated with the Government of Malaysia.
- **BUDI95 calculator:** Two sentences max. State that figures are estimates from average-style inputs, that actual quota depends on driving and load, and that eligibility is decided by the Government via MySubsidi, not this tool. Link to official programme pages where possible.
- **ASEAN comparison:** Two sentences max. Cross-country values use FX to USD (or MYR equivalent from USD). Retail sources update on different schedules. Point users to source and timestamp on the block.
- **News:** Headlines come from Google News RSS. RONradar does not edit, endorse, or verify linked articles.
- **FAQ:** Information is for consumer understanding only. Official policy comes from Ministry of Finance and KPDN announcements.

## 5. Numbers and units

- Always include unit and currency for prices: **RM 2.60/litre**, not "2.60" alone.
- Match decimal places to the source. Retail fuel in RM uses **two** decimals. FX rates in copy use **four** decimals where shown (for example MYR/USD).
- Week-on-week change: **one** decimal place for percentage, with arrow and colour. Use **▲** for increases and **▼** for decreases, and **▬** or plain text for flat. Pair with plain wording: "down RM 0.05 from last week" instead of "-RM 0.05" without context.
- Dates in **DD MMM YYYY** (for example **16 Apr 2026**).

## 6. What RONradar does not do

State clearly in FAQ or About:

- It does not predict future fuel prices.
- It does not give financial or investment advice.
- It does not verify BUDI95 or SPCS eligibility. Only MySubsidi and KPDN can do that.
- It does not track individual petrol stations. Figures are national APM prices, not station-level.
- It does not store or sell data you type into calculators (all runs in the browser unless you add analytics later).

## 7. Language for uncertainty

Use consistently:

- **Data not yet available** when expected data has not arrived.
- **Last updated [date]** on every official data block.
- **Estimate based on [inputs]** on every calculated value.
- **Source: [name], retrieved [date]** for external facts.
- **This figure is approximate** when rounding or averaging was applied.

Avoid vague body copy like "around", "roughly", or "give or take". Prefer **approximately** or **estimated** only where accurate.

## 8. Accessibility and trust

- Every chart needs the **same numbers** in a **table** (for example under a "View data as table" disclosure).
- Calculated results should be reproducible from the same inputs and the same published prices until prices update.
- Put a **Sources** link or line next to each data block, not only in the footer.

## 9. Do not ship

- Fake testimonials, placeholder reviews, or "trusted by X users" without real evidence.
- Lorem ipsum.
- Generic lines like "Welcome to the future of fuel tracking in Malaysia".
- Anything that implies government endorsement, partnership, or official status.
- **Emojis in body copy.** Icons (Material Symbols, arrows) are fine.

## 10. When unsure

If you are not sure a sentence is accurate, use a `{{TODO: verify}}` placeholder or leave a code comment. Never ship a confident claim without a source.

## 11. BUDI95 policy changes

If BUDI95 eligibility rules or the subsidised rate change, update on-site copy within **24 hours**. Never show outdated subsidy information as current.
