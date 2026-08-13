'use client';

import React from 'react';
import { DollarSign, PieChart, ShieldCheck, ArrowUpRight } from 'lucide-react';

export default function PortfolioPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Quantara Portfolio Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            Multi-asset portfolio valuation, USDT cash allocation, unrealized PnL, and exposure breakdown.
          </p>
        </div>
        <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-bold rounded-full border border-emerald-500/30">
          INDEPENDENT PORTFOLIO ENGINE
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-6">
          <span className="text-xs text-slate-400 font-medium block mb-1">TOTAL PORTFOLIO VALUATION</span>
          <div className="text-3xl font-black text-white">$24,857.50</div>
          <span className="text-xs text-emerald-400 font-bold flex items-center mt-2">
            <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" /> +15.4% Net Return
          </span>
        </div>

        <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-6">
          <span className="text-xs text-slate-400 font-medium block mb-1">USDT CASH BALANCE</span>
          <div className="text-3xl font-black text-emerald-400">$10,000.00</div>
          <span className="text-xs text-slate-500 block mt-2">40.2% Available Capital</span>
        </div>

        <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-6">
          <span className="text-xs text-slate-400 font-medium block mb-1">TOTAL DEPLOYED EXPOSURE</span>
          <div className="text-3xl font-black text-blue-400">$14,857.50</div>
          <span className="text-xs text-slate-500 block mt-2">59.8% Total Portfolio Exposure</span>
        </div>
      </div>

      {/* Asset Exposure Breakdown Table */}
      <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Asset Allocation Breakdown</h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Asset / Currency</th>
                <th className="py-3 px-4 text-right">Holdings</th>
                <th className="py-3 px-4 text-right">Avg Entry Price</th>
                <th className="py-3 px-4 text-right">Market Price</th>
                <th className="py-3 px-4 text-right">Position Value</th>
                <th className="py-3 px-4 text-right">Unrealized PnL</th>
                <th className="py-3 px-4 text-right">Exposure %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              <tr>
                <td className="py-3.5 px-4 font-bold text-emerald-400">USDT (Tether Cash)</td>
                <td className="py-3.5 px-4 text-right font-mono">$10,000.00</td>
                <td className="py-3.5 px-4 text-right font-mono">$1.00</td>
                <td className="py-3.5 px-4 text-right font-mono">$1.00</td>
                <td className="py-3.5 px-4 text-right font-mono">$10,000.00</td>
                <td className="py-3.5 px-4 text-right font-mono text-slate-500">$0.00</td>
                <td className="py-3.5 px-4 text-right font-mono font-bold">40.2%</td>
              </tr>
              <tr>
                <td className="py-3.5 px-4 font-bold text-white">BTC / USDT</td>
                <td className="py-3.5 px-4 text-right font-mono">0.1500 BTC</td>
                <td className="py-3.5 px-4 text-right font-mono">$61,000.00</td>
                <td className="py-3.5 px-4 text-right font-mono">$64,250.00</td>
                <td className="py-3.5 px-4 text-right font-mono">$9,637.50</td>
                <td className="py-3.5 px-4 text-right font-mono text-emerald-400 font-bold">+$487.50</td>
                <td className="py-3.5 px-4 text-right font-mono font-bold">38.8%</td>
              </tr>
              <tr>
                <td className="py-3.5 px-4 font-bold text-white">ETH / USDT</td>
                <td className="py-3.5 px-4 text-right font-mono">1.5000 ETH</td>
                <td className="py-3.5 px-4 text-right font-mono">$3,235.00</td>
                <td className="py-3.5 px-4 text-right font-mono">$3,480.00</td>
                <td className="py-3.5 px-4 text-right font-mono">$5,220.00</td>
                <td className="py-3.5 px-4 text-right font-mono text-emerald-400 font-bold">+$367.50</td>
                <td className="py-3.5 px-4 text-right font-mono font-bold">21.0%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
