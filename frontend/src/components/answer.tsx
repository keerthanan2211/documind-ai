'use client';

import { Fragment, useState } from 'react';
import clsx from 'clsx';
import { splitCitations } from '@/lib/citations';
import type { Message } from '@/lib/types';

/**
 * Renders an answer with clickable citation markers. Each marker jumps to and highlights
 * the matching source excerpt, which shows its page number, so readers can verify the claim.
 */
export function Answer({ message }: { message: Message }) {
  const [active, setActive] = useState<number | null>(null);
  const sources = message.sources ?? [];
  const anchor = (n: number) => `m${message.id}-s${n}`;

  return (
    <div>
      <div className="whitespace-pre-wrap font-serif text-[17px] leading-relaxed">
        {splitCitations(message.content).map((seg, i) =>
          seg.type === 'text' ? (
            <Fragment key={i}>{seg.text}</Fragment>
          ) : sources.some((s) => s.number === seg.number) ? (
            <a
              key={i}
              href={`#${anchor(seg.number)}`}
              onClick={() => setActive(seg.number)}
              className="mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded bg-mark px-1 align-super font-sans text-[11px] font-bold text-ink no-underline hover:bg-mark-edge"
              aria-label={`Source ${seg.number}, page ${sources.find((s) => s.number === seg.number)?.page}`}
            >
              {seg.number}
            </a>
          ) : null,
        )}
      </div>

      {sources.length > 0 && (
        <ol className="mt-4 space-y-2" aria-label="Sources">
          {sources.map((s) => (
            <li
              key={s.number}
              id={anchor(s.number)}
              className={clsx(
                'scroll-mt-24 rounded-md border-l-4 bg-shelf px-4 py-3 text-sm transition-colors',
                active === s.number ? 'border-mark-edge bg-mark/40' : 'border-mark',
              )}
            >
              <p className="font-bold">
                [{s.number}] Page {s.page}
              </p>
              <p className="mt-1 font-serif leading-relaxed text-ink/80">{s.excerpt}</p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
