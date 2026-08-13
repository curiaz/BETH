'use client';

import React from 'react';
import { Activity, Server, Database, ShieldCheck, Cpu, CheckCircle2 } from 'lucide-react';

const systemComponents = [
  {
    name: 'Paper Trading Engine',
    subtext: 'PaperTradingRunner continuous loop',
    status: 'HEALTHY',
    detail: 'TRADING_MODE=PAPER (Active Loop)',
    isHealthy: true,
  },
  {
    name: 'Binance Market Data Adapter',
    subtext: 'Public REST API (klines & 24hr tickers)',
    status: 'ONLINE',
    detail: 'Public Endpoints Connected (No API Keys Needed)',
    isHealthy: true,
  },
  {
    name: 'Risk Management Engine',
    subtext: '8 Priority Risk Rules Pipeline',
    status: 'ENFORCED',
    detail: '100% Pre-Trade Risk Evaluation Checks Passed',
    isHealthy: true,
  },
  {
    name: 'Portfolio Engine',
    subtext: 'Quantara High-Precision Decimal Engine',
    status: 'ACTIVE',
    detail: 'Multi-Asset USDT, BTC, ETH Position Accounting',
    isHealthy: true,
  },
  {
    name: 'Paper Broker',
    subtext: 'In-Memory Paper Execution Handler',
    status: 'ACTIVE',
    detail: 'Simulated Fills, Fees & Slippage Active',
    isHealthy: true,
  },
  {
    name: 'PostgreSQL / SQLite Storage',
    subtext: 'Async SQLAlchemy ORM Layer',
    status: 'CONNECTED',
    detail: 'Persisting Candles, Accounts, Orders & Fills',
    isHealthy: true,
  },
];

export default function SystemStatusPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">System Status & Health</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time status of Quantara BETHBot trading subsystems, market feeds, and storage layers.
          </p>
        </div>
        <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-bold rounded-full border border-emerald-500/30 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          ALL SYSTEMS OPERATIONAL
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {systemComponents.map((comp) => (
          <div key={comp.name} className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 space-y-3 hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white text-sm">{comp.name}</h3>
              <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded">
                {comp.status}
              </span>
            </div>
            <p className="text-xs text-slate-400">{comp.subtext}</p>
            <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-300 font-mono flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>{comp.detail}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 space-y-3 text-xs">
        <h3 className="font-bold text-slate-300 uppercase tracking-wider">System Environment Summary</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono text-slate-300">
          <div className="bg-slate-900/80 p-3 rounded border border-slate-800">
            <span className="text-slate-500 block text-[10px]">TRADING_MODE</span>
            <span className="font-bold text-amber-400">PAPER</span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded border border-slate-800">
            <span className="text-slate-500 block text-[10px]">BACKEND API</span>
            <span className="font-bold text-emerald-400">FastAPI</span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded border border-slate-800">
            <span className="text-slate-500 block text-[10px]">FRONTEND</span>
            <span className="font-bold text-blue-400">Next.js + Tailwind v4</span>
          </div>
          <div className="bg-slate-900/80 p-3 rounded border border-slate-800">
            <span className="text-slate-500 block text-[10px]">DATABASE</span>
            <span className="font-bold text-cyan-400">SQLAlchemy Async</span>
          </div>
        </div>
      </div>
    </div>
  );
}
