import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Macro Investment Intelligence — Market Regime Dashboard',
  description: 'Quantitative macroeconomic intelligence platform & market regime identification engine',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0B0F19] text-gray-100 antialiased selection:bg-brand-blue selection:text-white">
        {children}
      </body>
    </html>
  );
}
