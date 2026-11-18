'use client';

import Link from 'next/link';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { formatSize } from '@/lib/citations';
import type { DocumentInfo } from '@/lib/types';

const dateFormat = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short' });

export function DocumentList() {
  const qc = useQueryClient();
  const { data: docs, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: api.listDocuments,
    // Keep polling while anything is still being processed
    refetchInterval: (q) => (q.state.data?.some((d) => d.status === 'processing') ? 2000 : false),
  });
  const remove = useMutation({
    mutationFn: api.remove,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  });

  if (isLoading) return <p className="py-8 text-sm text-muted">Loading your documents…</p>;
  if (error) return <p role="alert" className="py-8 text-sm text-alert">{error.message}</p>;
  if (!docs?.length) return <p className="py-8 text-sm text-muted">No documents yet. Upload a PDF to start asking questions.</p>;

  return (
    <ul className="divide-y divide-rule border-y border-rule" aria-live="polite">
      {docs.map((doc) => (
        <li key={doc.id} className="flex items-center gap-4 py-4">
          <div className="min-w-0 flex-1">
            {doc.status === 'ready' ? (
              <Link href={`/documents/${doc.id}`} className="block truncate font-bold hover:underline">
                {doc.filename}
              </Link>
            ) : (
              <p className="truncate font-bold">{doc.filename}</p>
            )}
            <p className="mt-0.5 text-sm text-muted">
              <StatusText doc={doc} />
            </p>
          </div>
          {doc.status === 'ready' && (
            <Link href={`/documents/${doc.id}`} className="h-9 rounded-md border border-rule px-3 text-sm leading-9 hover:border-pine">
              Ask questions<span className="sr-only"> about {doc.filename}</span>
            </Link>
          )}
          <button
            type="button"
            className="text-sm text-muted underline hover:text-alert"
            disabled={remove.isPending}
            onClick={() => window.confirm(`Delete “${doc.filename}” and its conversation?`) && remove.mutate(doc.id)}
          >
            Delete<span className="sr-only"> {doc.filename}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}

function StatusText({ doc }: { doc: DocumentInfo }) {
  if (doc.status === 'processing') return <>Reading and indexing…</>;
  if (doc.status === 'failed') return <span className="text-alert">Couldn’t process: {doc.error}</span>;
  return (
    <>
      {doc.page_count} {doc.page_count === 1 ? 'page' : 'pages'}, {formatSize(doc.size_bytes)}, added {dateFormat.format(new Date(doc.created_at))}
    </>
  );
}
