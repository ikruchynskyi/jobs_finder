import './globals.css';
import type { Metadata } from 'next';
import { Outfit } from 'next/font/google';
import { Providers } from '@/components/providers';
import { Toaster } from 'react-hot-toast';

const outfit = Outfit({ 
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'AutoApply - Automate Your Job Applications',
  description: 'AI-powered job application automation platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={outfit.variable}>
        <Providers>
          {children}
          <Toaster 
            position="top-right"
            toastOptions={{
              className: 'glass',
              duration: 3000,
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
