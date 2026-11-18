'use client';

import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { DocumentInfo, Message } from '@/lib/types';
import { Answer } from './answer';

const SUGGESTIONS = ['Summarise this document in five points', 'What are the key dates or deadlines?', 'What does it say about costs or fees?'];

export function Chat({ doc }: { doc: DocumentInfo }) {
  const qc = useQueryClient();
  const key = ['messages', doc.id];
  const { data: messages = [], isLoading } = useQuery({ queryKey: key, queryFn: () => api.getMessages(doc.id) });
  const [question, setQuestion] = useState('');
  const [pending, setPending] = useState<string | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  const ask = useMutation({
    mutationFn: (q: string) => api.ask(doc.id, q),
    onMutate: (q) => setPending(q),
    onSuccess: ({ question: qMsg, answer }) => {
      qc.setQueryData<Message[]>(key, (old = []) => [...old, qMsg, answer]);
      setQuestion('');
    },
    onSettled: () => setPending(null),
  });

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages.length, pending]);

  const submit = (q: string) => {
    const trimmed = q.trim();
    if (trimmed.length >= 2 && !ask.isPending) ask.mutate(trimmed);
  };

  return (
    <div className="flex min-h-[60vh] flex-col">
      <div className="flex-1 space-y-8" aria-live="polite">
        {isLoading && <p className="text-sm text-muted">Loading conversation…</p>}

        {!isLoading && messages.length === 0 && !pending && (
          <div>
            <p className="text-muted">Ask anything about this document. Try one of these:</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} type="button" onClick={() => submit(s)} className="rounded-full border border-rule px-4 py-1.5 text-sm hover:border-pine">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) =>
          m.role === 'user' ? (
            <p key={m.id} className="ml-auto max-w-[85%] rounded-lg bg-pine-soft px-4 py-2.5 sm:max-w-[70%]">
              <span className="sr-only">You asked: </span>
              {m.content}
            </p>
          ) : (
            <section key={m.id} aria-label="Answer">
              <Answer message={m} />
            </section>
          ),
        )}

        {pending && (
          <>
            <p className="ml-auto max-w-[85%] rounded-lg bg-pine-soft px-4 py-2.5 sm:max-w-[70%]">{pending}</p>
            <p role="status" className="text-sm text-muted">
              Searching the document and writing an answer…
            </p>
          </>
        )}
        <div ref={bottom} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(question);
        }}
        className="sticky bottom-0 mt-8 border-t border-rule bg-white py-4"
      >
        {ask.error && (
          <p role="alert" className="mb-2 text-sm text-alert">
            {ask.error.message}
          </p>
        )}
        <label htmlFor="question" className="sr-only">
          Ask a question about {doc.filename}
        </label>
        <div className="flex gap-2">
          <textarea
            id="question"
            rows={1}
            value={question}
            maxLength={1000}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submit(question);
              }
            }}
            placeholder="Ask a question about this document"
            className="min-h-11 flex-1 resize-none rounded-md border border-rule px-3 py-2.5 focus:border-pine focus:outline-none"
          />
          <button type="submit" disabled={ask.isPending || question.trim().length < 2} className="h-11 rounded-md bg-pine px-5 font-bold text-white hover:bg-pine-dark disabled:opacity-50">
            Ask
          </button>
        </div>
        <p className="mt-1.5 text-xs text-muted">Enter to send, Shift+Enter for a new line. Answers come only from this document.</p>
      </form>
    </div>
  );
}
