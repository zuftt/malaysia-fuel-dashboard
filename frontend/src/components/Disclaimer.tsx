import type { ReactNode } from 'react';

type Tone = 'neutral' | 'amber' | 'info';

type Props = {
  title?: string;
  tone?: Tone;
  children: ReactNode;
  icon?: 'info' | 'warning';
  defaultOpen?: boolean;
  className?: string;
};

const toneStyles: Record<Tone, { wrap: string; summary: string; body: string; marker: string }> = {
  neutral: {
    wrap: 'border-l-2 border-l-[#1a1a1a] border-y border-r border-[#e5e5e0] bg-[#fafaf7]',
    summary: 'text-[#0a0a0a]',
    body: 'text-[#2a2a28]',
    marker: 'bg-[#1a1a1a] text-[#fafaf7]',
  },
  amber: {
    wrap: 'border-l-2 border-l-[#c24300] border-y border-r border-[#e8ddc6] bg-[#fdf6e9]',
    summary: 'text-[#3a2600]',
    body: 'text-[#3a2600]',
    marker: 'bg-[#c24300] text-white',
  },
  info: {
    wrap: 'border-l-2 border-l-[#0b5cad] border-y border-r border-[#d6e3f1] bg-[#eef4fb]',
    summary: 'text-[#07315c]',
    body: 'text-[#07315c]',
    marker: 'bg-[#0b5cad] text-white',
  },
};

export function Disclaimer({
  title = 'Note',
  tone = 'neutral',
  icon = 'info',
  defaultOpen = false,
  className,
  children,
}: Props) {
  const t = toneStyles[tone];
  const symbol = icon === 'warning' ? '!' : 'i';
  return (
    <details
      className={`disclosure ${t.wrap} ${className ?? ''}`}
      {...(defaultOpen ? { open: true } : {})}
    >
      <summary
        className={`flex items-center gap-2.5 px-3 py-2 text-[11px] font-semibold tracking-[0.14em] uppercase mono ${t.summary}`}
      >
        <span
          className={`inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold ${t.marker}`}
          aria-hidden
        >
          {symbol}
        </span>
        <span className="flex-1">{title}</span>
        <span className="chev text-[#6b6b68] text-xs leading-none" aria-hidden>
          ›
        </span>
      </summary>
      <div className={`px-3 pb-3 pt-1 text-[13px] leading-relaxed ${t.body}`}>{children}</div>
    </details>
  );
}
