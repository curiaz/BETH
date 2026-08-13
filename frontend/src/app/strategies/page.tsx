'use client';

import React from 'react';
import { Cpu, ShieldAlert, CheckCircle2, Lock } from 'lucide-react';

const strategies = [
  {
    id: 'sma_crossover',
    name: 'Moving Average Crossover',
    version: '1.0.0',
    description: 'Generates BUY signals on Golden Cross (Fast SMA > Slow SMA) and SELL signals on Death Cross.',
    symbols: ['BTC/USDT', 'ETH/USDT'],
    parameters: [
      { name: 'fast_period', default: 20, type: 'int' },
      { name: 'slow_period', default: 50, type: 'int' },
      { name: 'ma_type', default: 'SMA', type: 'str' },
    ],
    encapsulationRules: [
      'NO order placement capabilities',
      'NO direct exchange API access',
      'NO portfolio balance modifications',
      'NO direct database writes',
    ],
  },
  {
    id: 'rsi_mean_reversion',
    name: 'RSI Mean Reversion',
    version: '1.0.0',
    description: 'Identifies oversold (RSI < 30) buy opportunities and overbought (RSI > 70) sell opportunities.',
    symbols: ['BTC/USDT', 'ETH/USDT'],
    parameters: [
      { name: 'rsi_period', default: 14, type: 'int' },
      { name: 'oversold_threshold', default: 30, type: 'int' },
      { name: 'overbought_threshold', default: 70, type: 'int' },
    ],
    encapsulationRules: [
      'NO order placement capabilities',
      'NO direct exchange API access',
      'NO portfolio balance modifications',
      'NO direct database writes',
    ],
  },
];

export default function StrategiesPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Strategy Framework</h1>
          <p className="text-xs text-slate-400 mt-1">
            Registered trading strategies operating under strict encapsulation rules.
          </p>
        </div>
        <span className="px-3 py-1 bg-blue-500/10 text-blue-400 text-xs font-bold rounded-full border border-blue-500/30">
          STRATEGY REGISTRY ACTIVE
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {strategies.map((strat) => (
          <div key={strat.id} className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-blue-500/20 text-blue-400 rounded-lg">
                  <Cpu className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">{strat.name}</h3>
                  <span className="text-xs text-slate-500 font-mono">id: {strat.id} | v{strat.version}</span>
                </div>
              </div>
              <span className="text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded">
                REGISTERED
              </span>
            </div>

            <p className="text-xs text-slate-300">{strat.description}</p>

            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Configurable Parameters</h4>
              <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 space-y-1.5 font-mono text-xs text-slate-300">
                {strat.parameters.map((p) => (
                  <div key={p.name} className="flex items-center justify-between">
                    <span>{p.name}</span>
                    <span className="text-blue-400 font-bold">{String(p.default)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Encapsulation Invariants</h4>
              <div className="space-y-1 text-[11px] text-slate-400">
                {strat.encapsulationRules.map((rule, idx) => (
                  <div key={idx} className="flex items-center gap-1.5 text-emerald-400/90">
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                    <span>{rule}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
