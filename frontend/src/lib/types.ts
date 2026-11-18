export type DocStatus = 'processing' | 'ready' | 'failed';

export interface DocumentInfo {
  id: string;
  filename: string;
  size_bytes: number;
  page_count: number;
  chunk_count: number;
  status: DocStatus;
  error: string | null;
  created_at: string;
}

export interface Source {
  number: number;
  page: number;
  excerpt: string;
}

export interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  sources: Source[] | null;
  created_at: string;
}
