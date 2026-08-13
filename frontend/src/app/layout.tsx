import './globals.css';
import React from 'react';
import Link from 'next/link';

export const metadata = {
  title: 'BETHBot — Algorithmic Trading Platform',
  description: 'Professional Python algorithmic trading platform for BTC/USDT and ETH/USDT',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#0b0f19] text-slate-200 min-h-screen flex flex-col antialiased">
        <header className="border-b border-slate-800 bg-[#0f172a]/80 backdrop-blur sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-8">
              <Link href="/" className="flex items-center gap-2 font-bold text-xl text-blue-400">
                <span className="bg-blue-600 text-white px-2 py-0.5 rounded text-sm font-extrabold">
                  BETH
                </span>
                <span>Bot</span>
              </Link>
              <nav className="hidden md:flex gap-6 text-sm font-medium">
                <Link href="/" className="hover:text-blue-400 transition-colors">
                  Dashboard
                </Link>
                <Link href="/strategies" className="hover:text-blue-400 transition-colors">
                  Strategies
                </Link>
                <Link href="/backtests" className="hover:text-blue-400 transition-colors">
                  Backtests
                </Link>
                <Link href="/paper-trading" className="hover:text-blue-400 transition-colors">
                  Paper Trading
                </Link>
                <Link href="/portfolio" className="hover:text-blue-400 transition-colors">
                  Portfolio
                </Link>
              </nav>
            </div>
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                PAPER MODE
              </span>
              <Link
                href="/settings"
                className="p-2 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition-colors text-sm"
              >
                Settings
              </Link>
            </div>
          </div>
        </header>
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
          BETHBot Phase 1 — Backtest & Paper Trading Mode Only. No real money connections.
        </footer>
      </body>
    </html>
  );
}
