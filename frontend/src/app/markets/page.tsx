'use client';

import React from 'react';
import { ArrowUpRight, Activity, TrendingUp, BarChart2 } from 'lucide-react';

const marketsData = [
  {
    symbol: 'BTC/USDT',
    base: 'BTC',
    quote: 'USDT',
    name: 'Bitcoin',
    price: '$64,250.00',
    change24h: '+2.4%',
    isPositive: true,
    high24h: '$65,100.00',
    low24h: '$62,800.00',
    volume24h: '$1,420,500,000',
    status: 'ACTIVE TRADING PAIR',
  },
  {
    symbol: 'ETH/USDT',
    base: 'ETH',
    quote: 'USDT',
    name: 'Ethereum',
    price: '$3,480.00',
    change24h: '+1.8%',
    isPositive: true,
    high24h: '$3,520.00',
    low24h: '$3,410.00',
    volume24h: '$890,200,000',
    status: 'ACTIVE TRADING PAIR',
  },
];

export default function MarketsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Supported Markets</h1>
          <p className="text-xs text-slate-400 mt-1">
            Centralized market configuration system for BTC/USDT and ETH/USDT public market data.
          </p>
        </div>
        <span className="px-3 py-1 bg-blue-500/10 text-blue-400 text-xs font-bold rounded-full border border-blue-500/30">
          MARKET DATA SOURCE: BINANCE PUBLIC REST
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {marketsData.map((market) => (
          <div key={market.symbol} className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-6 space-y-4 hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-500/20 text-blue-400 font-black flex items-center justify-center text-sm">
                  {market.base}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">{market.symbol}</h3>
                  <span className="text-xs text-slate-400">{market.name}</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xl font-black text-white">{market.price}</div>
                <span className="text-xs font-bold text-emerald-400 flex items-center justify-end">
                  <ArrowUpRight className="w-3.5 h-3.5" /> {market.change24h}
                </span>
              </div>
            </div>

            <div className="border-t border-slate-800 pt-4 grid grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-slate-500 block">24h High</span>
                <span className="font-bold text-slate-200">{market.high24h}</span>
              </div>
              <div>
                <span className="text-slate-500 block">24h Low</span>
                <span className="font-bold text-slate-200">{market.low24h}</span>
              </div>
              <div>
                <span className="text-slate-500 block">24h Volume</span>
                <span className="font-bold text-slate-200">{market.volume24h}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Status</span>
                <span className="font-bold text-emerald-400">{market.status}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
