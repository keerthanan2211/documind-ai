import { DocumentList } from '@/components/document-list';
import { UploadZone } from '@/components/upload-zone';

export default function LibraryPage() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-serif text-4xl font-semibold leading-tight">Ask your documents</h1>
      <p className="mt-3 max-w-xl text-muted">
        Upload a PDF, then ask questions in plain language. Every answer shows the passages and page numbers it came from, so you can check it.
      </p>
      <div className="mt-8">
        <UploadZone />
      </div>
      <h2 className="mt-12 mb-2 font-bold">Your documents</h2>
      <DocumentList />
    </main>
  );
}
