'use client';

import { useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import clsx from 'clsx';
import { api } from '@/lib/api';

const MAX_MB = 20;

export function UploadZone() {
  const qc = useQueryClient();
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const upload = useMutation({
    mutationFn: api.upload,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  });

  const handle = (file: File | undefined) => {
    setLocalError(null);
    if (!file) return;
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setLocalError('Only PDF files can be uploaded.');
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setLocalError(`That file is over ${MAX_MB} MB. Try a smaller PDF.`);
      return;
    }
    upload.mutate(file);
  };

  const error = localError ?? upload.error?.message;

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handle(e.dataTransfer.files[0]);
        }}
        className={clsx(
          'flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors',
          dragging ? 'border-pine bg-pine-soft' : 'border-rule bg-shelf',
        )}
      >
        <p className="font-bold">Drop a PDF here</p>
        <p className="mt-1 text-sm text-muted">Text-based PDFs up to {MAX_MB} MB: manuals, contracts, papers, policies</p>
        <button
          type="button"
          onClick={() => input.current?.click()}
          disabled={upload.isPending}
          className="mt-4 h-10 rounded-md bg-pine px-5 text-sm font-bold text-white hover:bg-pine-dark disabled:opacity-60"
        >
          {upload.isPending ? 'Uploading…' : 'Choose a file'}
        </button>
        <input
          ref={input}
          type="file"
          accept="application/pdf,.pdf"
          className="sr-only"
          aria-label="Choose a PDF to upload"
          onChange={(e) => {
            handle(e.target.files?.[0]);
            e.target.value = '';
          }}
        />
      </div>
      {error && (
        <p role="alert" className="mt-3 text-sm text-alert">
          {error}
        </p>
      )}
    </div>
  );
}
