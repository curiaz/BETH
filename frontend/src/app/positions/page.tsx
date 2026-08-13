'use client';

import React from 'react';
import { Layers, ArrowUpRight, Lock } from 'lucide-react';

export default function PositionsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Active Positions</h1>
          <p className="text-xs text-slate-400 mt-1">
            Simultaneous open positions in BTC/USDT and ETH/USDT under risk manager limits.
          </p>
        </div>
        <span className="px-3 py-1 bg-amber-500/10 text-amber-400 text-xs font-bold rounded-full border border-amber-500/30">
          READ-ONLY POSITIONS VIEW
        </span>
      </div>

      <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Open Positions (2 / 2 Max Allowed)</h3>
          <span className="text-xs text-slate-500">Auto-Managed by RiskEngine</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Symbol</th>
                <th className="py-3 px-4">Side</th>
                <th className="py-3 px-4 text-right">Quantity</th>
                <th className="py-3 px-4 text-right">Avg Entry Price</th>
                <th className="py-3 px-4 text-right">Current Price</th>
                <th className="py-3 px-4 text-right">Position Value</th>
                <th className="py-3 px-4 text-right">Unrealized PnL</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              <tr>
                <td className="py-4 px-4 font-bold text-white flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 font-extrabold flex items-center justify-center text-[10px]">
                    ₿
                  </div>
                  BTC / USDT
                </td>
                <td className="py-4 px-4">
                  <span className="bg-emerald-500/10 text-emerald-400 font-bold px-2 py-0.5 rounded text-[10px]">
                    LONG
                  </span>
                </td>
                <td className="py-4 px-4 text-right font-mono font-bold">0.1500 BTC</td>
                <td className="py-4 px-4 text-right font-mono">$61,000.00</td>
                <td className="py-4 px-4 text-right font-mono">$64,250.00</td>
                <td className="py-4 px-4 text-right font-mono font-bold">$9,637.50</td>
                <td className="py-4 px-4 text-right font-mono text-emerald-400 font-bold">+$487.50 (+5.3%)</td>
                <td className="py-4 px-4 text-center">
                  <span className="inline-flex items-center gap-1 text-[10px] text-slate-500 bg-slate-800 px-2 py-1 rounded cursor-not-allowed">
                    <Lock className="w-3 h-3" /> Read-Only
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-4 px-4 font-bold text-white flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-400 font-extrabold flex items-center justify-center text-[10px]">
                    Ξ
                  </div>
                  ETH / USDT
                </td>
                <td className="py-4 px-4">
                  <span className="bg-emerald-500/10 text-emerald-400 font-bold px-2 py-0.5 rounded text-[10px]">
                    LONG
                  </span>
                </td>
                <td className="py-4 px-4 text-right font-mono font-bold">1.5000 ETH</td>
                <td className="py-4 px-4 text-right font-mono">$3,235.00</td>
                <td className="py-4 px-4 text-right font-mono">$3,480.00</td>
                <td className="py-4 px-4 text-right font-mono font-bold">$5,220.00</td>
                <td className="py-4 px-4 text-right font-mono text-emerald-400 font-bold">+$367.50 (+7.5%)</td>
                <td className="py-4 px-4 text-center">
                  <span className="inline-flex items-center gap-1 text-[10px] text-slate-500 bg-slate-800 px-2 py-1 rounded cursor-not-allowed">
                    <Lock className="w-3 h-3" /> Read-Only
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
