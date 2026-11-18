import type { DocumentInfo, Message } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api${path}`, init);
  } catch {
    throw new Error('Can’t reach the server. Check that the backend is running.');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = body?.detail;
    // FastAPI validation errors are a list; everything else is a string
    throw new Error(Array.isArray(detail) ? detail[0]?.msg ?? 'Invalid request' : detail ?? `Request failed (${res.status})`);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

export const api = {
  listDocuments: () => request<DocumentInfo[]>('/documents'),
  getDocument: (id: string) => request<DocumentInfo>(`/documents/${id}`),
  getMessages: (id: string) => request<Message[]>(`/documents/${id}/messages`),
  upload: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<DocumentInfo>('/documents', { method: 'POST', body: form });
  },
  remove: (id: string) => request<void>(`/documents/${id}`, { method: 'DELETE' }),
  ask: (id: string, question: string) =>
    request<{ question: Message; answer: Message }>(`/documents/${id}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    }),
};
