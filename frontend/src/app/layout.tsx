import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Data Janitor',
  description: 'Autonomous CRM data cleaning micro-SaaS',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
