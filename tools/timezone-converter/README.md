# ⏰ Timezone Converter CLI

A lightweight, production-ready timezone converter and meeting scheduler built with TypeScript.

**Features:**
- ⚡ Lightning-fast timezone conversion
- 📅 Smart meeting time scheduler (finds best times across zones)
- 🌍 Support for 10+ major timezones
- 🎨 Beautiful CLI with chalk styling
- 📦 Use as CLI tool OR import as library
- 🧪 Fully typed (TypeScript)

## Installation

```bash
npm install -g @zafri/timezone-converter
```

Or locally:
```bash
npm install @zafri/timezone-converter
```

## Usage

### CLI

**Convert time to multiple timezones:**
```bash
tzc convert "2026-03-28 14:30" -f kl -t ny,london,tokyo
```

**Show current time worldwide:**
```bash
tzc now --timezones kl,ny,london,sg,tokyo
```

**Find best meeting time:**
```bash
tzc meeting --timezones kl,ny,london,tokyo
```

### As a Library

```typescript
import TimezoneConverter from '@zafri/timezone-converter';

// Convert time
const results = TimezoneConverter.convert(
  '2026-03-28T14:30:00Z',
  'kl',
  ['ny', 'london', 'tokyo']
);

// Find meeting times
const schedule = TimezoneConverter.findBestMeetingTime(['kl', 'ny', 'london']);
```

## Supported Timezones

| Code | Timezone |
|------|----------|
| kl | Asia/Kuala_Lumpur |
| sg | Asia/Singapore |
| hk | Asia/Hong_Kong |
| jp | Asia/Tokyo |
| ny | America/New_York |
| la | America/Los_Angeles |
| london | Europe/London |
| dubai | Asia/Dubai |
| sydney | Australia/Sydney |
| auckland | Pacific/Auckland |

## Architecture

- **index.ts** — Core library (exportable, no CLI code)
- **cli.ts** — CLI commands built on top of library
- **package.json** — Configured for both npm distribution and global CLI

Perfect for:
- Distributed teams coordinating across zones
- Meeting schedulers
- Time-sensitive applications
- DevOps/SRE dashboards

## License

MIT — Build on it, use it, share it.

---

Made by **Muhd Zafri** 🚀
