'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Chat } from '@/components/chat';
import { api } from '@/lib/api';
import { formatSize } from '@/lib/citations';

export default function DocumentPage() {
  const { id } = useParams<{ id: string }>();
  const { data: doc, isLoading, error } = useQuery({
    queryKey: ['document', id],
    queryFn: () => api.getDocument(id),
    refetchInterval: (q) => (q.state.data?.status === 'processing' ? 2000 : false),
  });

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <Link href="/" className="text-sm text-muted hover:text-ink">
        All documents
      </Link>

      {isLoading && <p className="mt-8 text-muted">Loading…</p>}
      {error && (
        <p role="alert" className="mt-8 text-alert">
          {error.message}
        </p>
      )}

      {doc && (
        <>
          <h1 className="mt-3 break-words font-serif text-3xl font-semibold">{doc.filename}</h1>
          <p className="mt-1 text-sm text-muted">
            {doc.page_count} pages, {formatSize(doc.size_bytes)}, {doc.chunk_count} indexed passages
          </p>
          <div className="mt-8">
            {doc.status === 'ready' && <Chat doc={doc} />}
            {doc.status === 'processing' && <p role="status">Still reading this document. This page will update when it’s ready.</p>}
            {doc.status === 'failed' && <p role="alert" className="text-alert">Couldn’t process this file: {doc.error}</p>}
          </div>
        </>
      )}
    </main>
  );
}
