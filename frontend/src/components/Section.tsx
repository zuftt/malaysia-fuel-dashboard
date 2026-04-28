import type { ReactNode } from 'react';

type Props = {
  id?: string;
  eyebrow?: string;
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  /** When true the section surface is omitted (caller renders its own panel). */
  bare?: boolean;
  className?: string;
};

export function Section({
  id,
  eyebrow,
  title,
  description,
  actions,
  children,
  bare = false,
  className,
}: Props) {
  return (
    <section id={id} className={`scroll-mt-24 ${className ?? ''}`}>
      <div className="border-b border-[#1a1a1a] pb-3 mb-4 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="min-w-0">
          {eyebrow && (
            <p className="eyebrow mb-1.5 inline-flex items-center gap-2 flex-wrap">
              <span>{eyebrow}</span>
            </p>
          )}
          <h2 className="serif text-xl sm:text-[26px] font-semibold text-[#0a0a0a] leading-tight">
            {title}
          </h2>
          {description && (
            <div className="mt-1.5 text-[14px] sm:text-[13px] text-[#4b4b48] max-w-3xl leading-relaxed">{description}</div>
          )}
        </div>
        {actions && <div className="flex flex-wrap gap-2 shrink-0">{actions}</div>}
      </div>
      {bare ? children : <div className="panel p-4 sm:p-5">{children}</div>}
    </section>
  );
}
