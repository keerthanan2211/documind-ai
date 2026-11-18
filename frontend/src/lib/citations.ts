export type Segment = { type: 'text'; text: string } | { type: 'cite'; number: number };

/** Splits "Lasts 24 months [1][2]." into text and citation segments so citations can render as links. */
export function splitCitations(answer: string): Segment[] {
  const segments: Segment[] = [];
  const pattern = /\[(\d+)\]/g;
  let last = 0;
  for (const match of answer.matchAll(pattern)) {
    if (match.index! > last) segments.push({ type: 'text', text: answer.slice(last, match.index) });
    segments.push({ type: 'cite', number: Number(match[1]) });
    last = match.index! + match[0].length;
  }
  if (last < answer.length) segments.push({ type: 'text', text: answer.slice(last) });
  return segments;
}

export function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
