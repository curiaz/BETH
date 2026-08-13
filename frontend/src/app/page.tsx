'use client';

import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  ShieldCheck,
  Zap,
  Lock,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  DollarSign,
  PieChart,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

// Sample performance equity curve data
const equityData = [
  { time: '00:00', equity: 24000 },
  { time: '04:00', equity: 24150 },
  { time: '08:00', equity: 24080 },
  { time: '12:00', equity: 24350 },
  { time: '16:00', equity: 24600 },
  { time: '20:00', equity: 24520 },
  { time: '24:00', equity: 24857.5 },
];

export default function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Read-Only Banner */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-500/20 rounded-lg text-amber-400">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-amber-300">Read-Only Paper Trading Mode Active</h4>
            <p className="text-xs text-amber-400/80">
              Live exchange order execution is disabled. All trades are executed against simulated paper balances.
            </p>
          </div>
        </div>
        <span className="px-3 py-1 bg-amber-500/20 text-amber-300 text-xs font-bold rounded-full border border-amber-500/40">
          TRADING_MODE = PAPER
        </span>
      </div>

      {/* Top Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Portfolio Value */}
        <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>TOTAL PORTFOLIO VALUE</span>
            <DollarSign className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-black text-white">$24,857.50</div>
          <div className="flex items-center gap-2 mt-2 text-xs">
            <span className="text-emerald-400 font-bold flex items-center">
              <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> +15.4%
            </span>
            <span className="text-slate-500">all-time net</span>
          </div>
        </div>

        {/* USDT Balance */}
        <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>USDT CASH BALANCE</span>
            <PieChart className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400">$10,000.00</div>
          <div className="text-xs text-slate-500 mt-2">Available unencumbered capital</div>
        </div>

        {/* Realized & Unrealized PnL */}
        <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>REALIZED & UNREALIZED P/L</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline gap-3">
            <span className="text-lg font-bold text-emerald-400">+$1,450.00</span>
            <span className="text-xs text-slate-500">realized</span>
          </div>
          <div className="flex items-baseline gap-3 mt-1">
            <span className="text-lg font-bold text-cyan-400">+$857.50</span>
            <span className="text-xs text-slate-500">unrealized</span>
          </div>
        </div>

        {/* Drawdown & Bot Status */}
        <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>DRAWDOWN & BOT STATUS</span>
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs text-slate-400">Max Drawdown</div>
              <div className="text-lg font-bold text-slate-200">-1.2%</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-400">Bot Engine</div>
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                ACTIVE
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Market Prices & Positions + Equity Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Prices & Positions */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-300 tracking-wider uppercase">Live Markets & Open Positions</h3>

          {/* BTC Card */}
          <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-amber-500/20 text-amber-400 font-black flex items-center justify-center text-xs">
                  ₿
                </div>
                <div>
                  <h4 className="font-bold text-white">BTC / USDT</h4>
                  <span className="text-xs text-slate-500">Bitcoin</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-white">$64,250.00</div>
                <span className="text-xs text-emerald-400 font-bold flex items-center justify-end">
                  <ArrowUpRight className="w-3.5 h-3.5" /> +2.4%
                </span>
              </div>
            </div>

            <div className="border-t border-slate-800/80 pt-3 grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-slate-500 block">Position</span>
                <span className="font-bold text-slate-200">0.1500 BTC</span>
              </div>
              <div>
                <span className="text-slate-500 block">Position Value</span>
                <span className="font-bold text-slate-200">$9,637.50</span>
              </div>
              <div>
                <span className="text-slate-500 block">Avg Entry Price</span>
                <span className="font-bold text-slate-200">$61,000.00</span>
              </div>
              <div>
                <span className="text-slate-500 block">Unrealized PnL</span>
                <span className="font-bold text-emerald-400">+$487.50 (+5.3%)</span>
              </div>
            </div>
          </div>

          {/* ETH Card */}
          <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-400 font-black flex items-center justify-center text-xs">
                  Ξ
                </div>
                <div>
                  <h4 className="font-bold text-white">ETH / USDT</h4>
                  <span className="text-xs text-slate-500">Ethereum</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-white">$3,480.00</div>
                <span className="text-xs text-emerald-400 font-bold flex items-center justify-end">
                  <ArrowUpRight className="w-3.5 h-3.5" /> +1.8%
                </span>
              </div>
            </div>

            <div className="border-t border-slate-800/80 pt-3 grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-slate-500 block">Position</span>
                <span className="font-bold text-slate-200">1.5000 ETH</span>
              </div>
              <div>
                <span className="text-slate-500 block">Position Value</span>
                <span className="font-bold text-slate-200">$5,220.00</span>
              </div>
              <div>
                <span className="text-slate-500 block">Avg Entry Price</span>
                <span className="font-bold text-slate-200">$3,235.00</span>
              </div>
              <div>
                <span className="text-slate-500 block">Unrealized PnL</span>
                <span className="font-bold text-emerald-400">+$367.50 (+7.5%)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Portfolio Equity Chart & Current Signals */}
        <div className="lg:col-span-2 space-y-6">
          {/* Equity Chart Card */}
          <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-300 tracking-wider uppercase">Portfolio Equity Growth</h3>
              <span className="text-xs text-slate-500 font-medium">Last 24 Hours</span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={equityData}>
                  <defs>
                    <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} domain={['dataMin - 100', 'dataMax + 100']} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    labelStyle={{ color: '#94a3b8' }}
                  />
                  <Area type="monotone" dataKey="equity" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorEquity)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Current Strategy Signals */}
          <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-bold text-slate-300 tracking-wider uppercase">Current Strategy Signals</h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-slate-900/90 border border-emerald-500/30 rounded-lg p-4 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-slate-400 block">BTC / USDT</span>
                  <span className="text-xs text-slate-500">Moving Average Crossover</span>
                </div>
                <div className="text-right">
                  <span className="inline-block px-3 py-1 rounded bg-emerald-500/20 text-emerald-400 font-extrabold text-xs">
                    BUY (0.85)
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-1">Golden Cross Detected</span>
                </div>
              </div>

              <div className="bg-slate-900/90 border border-slate-700/50 rounded-lg p-4 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-slate-400 block">ETH / USDT</span>
                  <span className="text-xs text-slate-500">Moving Average Crossover</span>
                </div>
                <div className="text-right">
                  <span className="inline-block px-3 py-1 rounded bg-slate-700 text-slate-300 font-extrabold text-xs">
                    HOLD (0.00)
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-1">No Crossover</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Trade Log Table */}
      <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-300 tracking-wider uppercase">Recent Paper Trades</h3>
          <span className="text-xs text-slate-500">Last 5 Simulated Fills</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Symbol</th>
                <th className="py-3 px-4">Side</th>
                <th className="py-3 px-4 text-right">Quantity</th>
                <th className="py-3 px-4 text-right">Fill Price</th>
                <th className="py-3 px-4 text-right">Fee (USDT)</th>
                <th className="py-3 px-4 text-right">Realized PnL</th>
                <th className="py-3 px-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              <tr>
                <td className="py-3 px-4 text-slate-400 font-mono">2026-08-13 12:45:10</td>
                <td className="py-3 px-4 font-bold text-white">BTC/USDT</td>
                <td className="py-3 px-4">
                  <span className="text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded">BUY</span>
                </td>
                <td className="py-3 px-4 text-right font-mono">0.0500</td>
                <td className="py-3 px-4 text-right font-mono">$64,100.00</td>
                <td className="py-3 px-4 text-right font-mono">$3.20</td>
                <td className="py-3 px-4 text-right font-mono text-slate-500">$0.00</td>
                <td className="py-3 px-4 text-center">
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">FILLED</span>
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 text-slate-400 font-mono">2026-08-13 11:20:04</td>
                <td className="py-3 px-4 font-bold text-white">ETH/USDT</td>
                <td className="py-3 px-4">
                  <span className="text-rose-400 font-bold bg-rose-500/10 px-2 py-0.5 rounded">SELL</span>
                </td>
                <td className="py-3 px-4 text-right font-mono">0.5000</td>
                <td className="py-3 px-4 text-right font-mono">$3,450.00</td>
                <td className="py-3 px-4 text-right font-mono">$1.72</td>
                <td className="py-3 px-4 text-right font-mono text-emerald-400 font-bold">+$125.00</td>
                <td className="py-3 px-4 text-center">
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">FILLED</span>
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 text-slate-400 font-mono">2026-08-13 09:15:33</td>
                <td className="py-3 px-4 font-bold text-white">BTC/USDT</td>
                <td className="py-3 px-4">
                  <span className="text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded">BUY</span>
                </td>
                <td className="py-3 px-4 text-right font-mono">0.1000</td>
                <td className="py-3 px-4 text-right font-mono">$61,000.00</td>
                <td className="py-3 px-4 text-right font-mono">$6.10</td>
                <td className="py-3 px-4 text-right font-mono text-slate-500">$0.00</td>
                <td className="py-3 px-4 text-center">
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">FILLED</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
