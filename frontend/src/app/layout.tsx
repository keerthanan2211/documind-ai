import type { Metadata } from 'next';
import { Atkinson_Hyperlegible, Source_Serif_4 } from 'next/font/google';
import Link from 'next/link';
import { Providers } from './providers';
import './globals.css';

const ui = Atkinson_Hyperlegible({ subsets: ['latin'], weight: ['400', '700'], variable: '--font-ui', display: 'swap' });
const read = Source_Serif_4({ subsets: ['latin'], weight: ['400', '600'], variable: '--font-read', display: 'swap' });

export const metadata: Metadata = {
  title: { default: 'DocuMind AI', template: '%s · DocuMind AI' },
  description: 'Ask questions about your PDFs and get answers that cite the page they came from.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${ui.variable} ${read.variable}`}>
      <body className="min-h-screen font-sans">
        <Providers>
          <header className="border-b border-rule">
            <div className="mx-auto flex h-14 max-w-6xl items-center px-4">
              <Link href="/" className="flex items-center gap-2 font-bold">
                <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden>
                  <rect x="2" y="2" width="12" height="16" rx="1.5" fill="none" stroke="#145C57" strokeWidth="1.8" />
                  <rect x="5" y="8" width="12" height="4" rx="1" fill="#FFE58A" />
                </svg>
                DocuMind
              </Link>
            </div>
          </header>
          {children}
        </Providers>
      </body>
    </html>
  );
}
