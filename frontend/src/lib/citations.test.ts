import { describe, expect, it } from 'vitest';
import { formatSize, splitCitations } from './citations';

describe('splitCitations', () => {
  it('separates text and citation markers', () => {
    expect(splitCitations('Lasts 24 months [1][2].')).toEqual([
      { type: 'text', text: 'Lasts 24 months ' },
      { type: 'cite', number: 1 },
      { type: 'cite', number: 2 },
      { type: 'text', text: '.' },
    ]);
  });

  it('returns plain text unchanged', () => {
    expect(splitCitations('No citations here')).toEqual([{ type: 'text', text: 'No citations here' }]);
  });

  it('ignores non-numeric brackets', () => {
    expect(splitCitations('See [a] and [12]')).toEqual([
      { type: 'text', text: 'See [a] and ' },
      { type: 'cite', number: 12 },
    ]);
  });
});

describe('formatSize', () => {
  it('formats kilobytes and megabytes', () => {
    expect(formatSize(500)).toBe('1 KB');
    expect(formatSize(250 * 1024)).toBe('250 KB');
    expect(formatSize(3.4 * 1024 * 1024)).toBe('3.4 MB');
  });
});
