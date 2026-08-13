'use client';

import React from 'react';

const tradeHistory = [
  {
    id: 'trd-1005',
    timestamp: '2026-08-13 12:45:10',
    symbol: 'BTC/USDT',
    side: 'BUY',
    quantity: '0.0500',
    price: '$64,100.00',
    fee: '$3.20',
    slippage: '$32.05',
    pnl: '$0.00',
    status: 'FILLED',
  },
  {
    id: 'trd-1004',
    timestamp: '2026-08-13 11:20:04',
    symbol: 'ETH/USDT',
    side: 'SELL',
    quantity: '0.5000',
    price: '$3,450.00',
    fee: '$1.72',
    slippage: '$1.72',
    pnl: '+$125.00',
    status: 'FILLED',
  },
  {
    id: 'trd-1003',
    timestamp: '2026-08-13 09:15:33',
    symbol: 'BTC/USDT',
    side: 'BUY',
    quantity: '0.1000',
    price: '$61,000.00',
    fee: '$6.10',
    slippage: '$30.50',
    pnl: '$0.00',
    status: 'FILLED',
  },
  {
    id: 'trd-1002',
    timestamp: '2026-08-12 18:30:00',
    symbol: 'ETH/USDT',
    side: 'BUY',
    quantity: '2.0000',
    price: '$3,200.00',
    fee: '$6.40',
    slippage: '$3.20',
    pnl: '$0.00',
    status: 'FILLED',
  },
  {
    id: 'trd-1001',
    timestamp: '2026-08-12 14:10:15',
    symbol: 'BTC/USDT',
    side: 'SELL',
    quantity: '0.0800',
    price: '$62,500.00',
    fee: '$5.00',
    slippage: '$31.25',
    pnl: '+$320.00',
    status: 'FILLED',
  },
];

export default function TradesPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Trade Log & History</h1>
          <p className="text-xs text-slate-400 mt-1">
            Complete audit log of simulated paper trading fills, fees, slippage, and realized PnL.
          </p>
        </div>
        <span className="px-3 py-1 bg-blue-500/10 text-blue-400 text-xs font-bold rounded-full border border-blue-500/30">
          PAPER EXECUTION HISTORY
        </span>
      </div>

      <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Executed Fills History</h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Trade ID</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Symbol</th>
                <th className="py-3 px-4">Side</th>
                <th className="py-3 px-4 text-right">Quantity</th>
                <th className="py-3 px-4 text-right">Fill Price</th>
                <th className="py-3 px-4 text-right">Fee (USDT)</th>
                <th className="py-3 px-4 text-right">Slippage</th>
                <th className="py-3 px-4 text-right">Realized PnL</th>
                <th className="py-3 px-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {tradeHistory.map((trade) => (
                <tr key={trade.id}>
                  <td className="py-3.5 px-4 font-mono text-slate-400">{trade.id}</td>
                  <td className="py-3.5 px-4 font-mono text-slate-400">{trade.timestamp}</td>
                  <td className="py-3.5 px-4 font-bold text-white">{trade.symbol}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`font-bold px-2 py-0.5 rounded text-[10px] ${
                        trade.side === 'BUY'
                          ? 'bg-emerald-500/10 text-emerald-400'
                          : 'bg-rose-500/10 text-rose-400'
                      }`}
                    >
                      {trade.side}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono font-bold">{trade.quantity}</td>
                  <td className="py-3.5 px-4 text-right font-mono">{trade.price}</td>
                  <td className="py-3.5 px-4 text-right font-mono">{trade.fee}</td>
                  <td className="py-3.5 px-4 text-right font-mono text-slate-400">{trade.slippage}</td>
                  <td
                    className={`py-3.5 px-4 text-right font-mono font-bold ${
                      trade.pnl.startsWith('+') ? 'text-emerald-400' : 'text-slate-400'
                    }`}
                  >
                    {trade.pnl}
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                      {trade.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
