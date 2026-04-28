import type { NewsArticle } from '../lib/types';
import { formatRelativeMs, shortSourceLabel } from '../lib/formatters';
import { Disclaimer } from './Disclaimer';

type Props = {
  articles: NewsArticle[];
};

export function NewsGrid({ articles }: Props) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-end">
        <a
          href="https://webz.io/products/news-api"
          target="_blank"
          rel="noopener noreferrer"
          className="mono text-[11px] tracking-[0.12em] uppercase text-[#0a0a0a] underline decoration-[#1a1a1a] decoration-1 underline-offset-4 hover:decoration-[#c24300]"
        >
          Powered by Webz.io ›
        </a>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-0 panel">
        {articles.length === 0 ? (
          <div className="col-span-full px-6 py-10 text-center text-[#4b4b48]">
            <p className="text-[13px] mb-2">Data not yet available for this feed, or the API is still syncing.</p>
            <p className="text-[12px] opacity-80">Check that the backend can reach the Webz.io News API.</p>
          </div>
        ) : (
          articles.map((article, idx) => {
            const tag = article.announcement_type === 'News Feed' ? 'Feed' : article.announcement_type;
            const isFeed = article.announcement_type === 'News Feed';
            const tagStyle = isFeed ? 'text-[#c24300] border-[#c24300]' : 'text-[#4b4b48] border-[#4b4b48]';
            const href = article.source_url || '#';
            const rowBreak = 'md:[&:nth-child(2n)]:border-l md:[&:nth-child(2n)]:border-[#e5e5e0] lg:[&:nth-child(2n)]:border-l-0 lg:[&:nth-child(3n-1)]:border-x lg:[&:nth-child(3n-1)]:border-[#e5e5e0]';
            const CardInner = (
              <div className="p-4 flex flex-col h-full">
                <div className="flex items-center gap-2 mb-2">
                  <span className="mono text-[10px] text-[#6b6b68] tabular-nums">
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                  <span className={`mono text-[10px] font-bold uppercase tracking-[0.14em] px-1.5 py-0.5 border ${tagStyle}`}>
                    {tag}
                  </span>
                </div>
                <h3 className="serif font-semibold text-[16px] text-[#0a0a0a] leading-snug mb-2 group-hover:text-[#c24300] transition-colors">
                  {article.title}
                </h3>
                <p className="text-[12px] text-[#4b4b48] line-clamp-3 mb-3 flex-1 leading-relaxed">
                  {(article.content || '').replace(/\s+/g, ' ').slice(0, 200)}
                  {(article.content || '').length > 200 ? '…' : ''}
                </p>
                <div className="flex items-center gap-2 mono text-[10px] tracking-[0.08em] uppercase text-[#6b6b68] mt-auto pt-2 border-t border-[#e5e5e0]">
                  <span>{shortSourceLabel(article.source)}</span>
                  <span className="text-[#c5c5c0]">/</span>
                  <span>{formatRelativeMs(article.announcement_date)}</span>
                </div>
              </div>
            );
            const cellBorder = `border-b border-[#e5e5e0] ${rowBreak}`;
            return article.source_url ? (
              <a
                key={article.id}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className={`${cellBorder} hover:bg-[#fafaf7] transition-colors cursor-pointer group text-left no-underline`}
              >
                {CardInner}
              </a>
            ) : (
              <div key={article.id} className={`${cellBorder} group`}>
                {CardInner}
              </div>
            );
          })
        )}
      </div>
      <Disclaimer title="About these headlines" tone="neutral">
        <p>
          Headlines are pulled from the Webz.io News API. RONradar does not edit, endorse, or verify the content of linked
          articles. Links open in new tabs to the original publishers.
        </p>
      </Disclaimer>
    </div>
  );
}
