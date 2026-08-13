import './globals.css';
import React from 'react';
import Link from 'next/link';

export const metadata = {
  title: 'BETHBot — Professional Algorithmic Trading Platform',
  description: 'Automated quantitative paper-trading and backtesting engine for BTC/USDT and ETH/USDT',
};

const navItems = [
  { name: 'Dashboard', href: '/' },
  { name: 'Markets', href: '/markets' },
  { name: 'Portfolio', href: '/portfolio' },
  { name: 'Positions', href: '/positions' },
  { name: 'Trades', href: '/trades' },
  { name: 'Backtesting', href: '/backtesting' },
  { name: 'Strategies', href: '/strategies' },
  { name: 'Risk', href: '/risk' },
  { name: 'System Status', href: '/status' },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#0b0f19] text-slate-100 min-h-screen flex flex-col antialiased">
        {/* Navigation Bar */}
        <header className="border-b border-slate-800 bg-[#0f172a]/90 backdrop-blur sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Link href="/" className="flex items-center gap-2 font-bold text-xl text-blue-400 tracking-tight">
                <span className="bg-blue-600 text-white px-2 py-0.5 rounded text-sm font-black tracking-wider">
                  BETH
                </span>
                <span>Bot</span>
              </Link>

              <nav className="hidden lg:flex gap-4 text-xs font-semibold tracking-wide uppercase text-slate-400">
                {navItems.map((item) => (
                  <Link
                    key={item.name}
                    href={item.href}
                    className="hover:text-blue-400 transition-colors px-2 py-1 rounded hover:bg-slate-800/50"
                  >
                    {item.name}
                  </Link>
                ))}
              </nav>
            </div>

            <div className="flex items-center gap-3">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                READ-ONLY PAPER MODE
              </span>
            </div>
          </div>

          {/* Mobile sub-nav */}
          <div className="lg:hidden flex overflow-x-auto gap-3 px-4 py-2 border-t border-slate-800/60 text-xs font-medium text-slate-400 no-scrollbar">
            {navItems.map((item) => (
              <Link key={item.name} href={item.href} className="whitespace-nowrap hover:text-blue-400">
                {item.name}
              </Link>
            ))}
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500 bg-[#080b12]">
          BETHBot Phase 1 — Professional Paper Trading & Backtesting Platform. Read-Only Mode Active.
        </footer>
      </body>
    </html>
  );
}
