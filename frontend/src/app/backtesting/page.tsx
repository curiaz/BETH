'use client';

import React from 'react';
import { Play, BarChart2, AlertCircle, FileText, ArrowUpRight } from 'lucide-react';

export default function BacktestingPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Quantara Backtesting Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            Simulate strategies over historical OHLCV data sequentially without look-ahead bias.
          </p>
        </div>
        <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 text-xs font-bold rounded-full border border-indigo-500/30">
          SEQUENTIAL BACKTEST ENGINE
        </span>
      </div>

      {/* Backtest Controls & Asset Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Backtest Configuration */}
        <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Backtest Parameters</h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Strategy</label>
              <select className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200 font-medium">
                <option>Moving Average Crossover (sma_crossover)</option>
                <option>RSI Mean Reversion (rsi_mean_reversion)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Asset Symbol</label>
              <select className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200 font-medium">
                <option>BTC/USDT</option>
                <option>ETH/USDT</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-slate-400 mb-1">Fast Period</label>
                <input type="number" defaultValue={20} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200 font-mono" />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Slow Period</label>
                <input type="number" defaultValue={50} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200 font-mono" />
              </div>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Initial Capital (USDT)</label>
              <input type="number" defaultValue={10000} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200 font-mono" />
            </div>

            <button
              type="button"
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 rounded-lg flex items-center justify-center gap-2 transition-colors mt-2 text-xs"
            >
              <Play className="w-4 h-4" /> Run Simulated Backtest
            </button>
          </div>
        </div>

        {/* Backtest Performance Results Report */}
        <div className="lg:col-span-2 bg-[#0f172a]/80 border border-slate-800 rounded-xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">BacktestReport — BTC/USDT</h3>
              <span className="text-xs text-slate-500">Period: 2024-01-01 to 2026-08-13 (Hourly Candles)</span>
            </div>
            <span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-bold rounded">
              COMPLETED
            </span>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-500 block">Total Return</span>
              <span className="text-base font-black text-emerald-400">+24.50%</span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-500 block">Market Buy&Hold</span>
              <span className="text-base font-bold text-slate-300">+12.10%</span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-500 block">Strategy Alpha</span>
              <span className="text-base font-bold text-blue-400">+12.40%</span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-500 block">Sharpe Ratio</span>
              <span className="text-base font-bold text-slate-200">1.85</span>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-500 block">Win Rate</span>
              <span className="text-base font-bold text-slate-200">58.4%</span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-500 block">Profit Factor</span>
              <span className="text-base font-bold text-slate-200">1.92</span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-500 block">Max Drawdown</span>
              <span className="text-base font-bold text-rose-400">-4.20%</span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-500 block">Total Trades</span>
              <span className="text-base font-bold text-slate-200">48</span>
            </div>
          </div>

          {/* Statutory Disclaimer */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 text-[11px] text-slate-400 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <span>
              DISCLAIMER: Backtest performance metrics are historical simulations based on past market data.
              Simulated backtest results do NOT guarantee or imply profitability in live trading environments.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
