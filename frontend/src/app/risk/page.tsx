'use client';

import React from 'react';
import { ShieldCheck, AlertTriangle, Lock } from 'lucide-react';

const riskRules = [
  {
    name: 'Maximum Position Size',
    key: 'max_position_size_pct',
    value: '20.0%',
    description: 'Limits single position value to max 20% of total portfolio equity.',
    status: 'ACTIVE & ENFORCED',
  },
  {
    name: 'Maximum Portfolio Exposure',
    key: 'max_portfolio_exposure_pct',
    value: '80.0%',
    description: 'Limits total deployed position value to max 80% across all open positions (BTC + ETH).',
    status: 'ACTIVE & ENFORCED',
  },
  {
    name: 'Maximum Risk Per Trade',
    key: 'max_risk_per_trade_pct',
    value: '2.0%',
    description: 'Limits potential trade loss based on stop-loss distance.',
    status: 'ACTIVE & ENFORCED',
  },
  {
    name: 'Stop-Loss Validation',
    key: 'max_stop_loss_pct',
    value: '10.0%',
    description: 'Validates stop-loss placement below entry price and within 10% max distance.',
    status: 'ACTIVE & ENFORCED',
  },
  {
    name: 'Take-Profit Validation',
    key: 'min_reward_risk_ratio',
    value: '1.0x',
    description: 'Validates take-profit target price above entry price.',
    status: 'ACTIVE & ENFORCED',
  },
  {
    name: 'Maximum Daily Loss',
    key: 'max_daily_loss_pct',
    value: '3.0%',
    description: 'Halts new buy orders for the day if daily portfolio drawdown reaches 3%.',
    status: 'ACTIVE & ENFORCED',
  },
  {
    name: 'Maximum Open Positions',
    key: 'max_open_positions',
    value: '2 Positions',
    description: 'Limits simultaneous active positions across the portfolio (BTC/USDT, ETH/USDT).',
    status: 'ACTIVE & ENFORCED',
  },
  {
    name: 'Maximum Trades Per Day',
    key: 'max_trades_per_day',
    value: '10 Trades',
    description: 'Limits maximum executed trades per day to prevent overtrading.',
    status: 'ACTIVE & ENFORCED',
  },
];

export default function RiskPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Risk Management Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            Pre-trade order evaluation pipeline executing 8 configurable risk rules before order submission.
          </p>
        </div>
        <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-bold rounded-full border border-emerald-500/30">
          RISK PIPELINE ACTIVE (8 RULES)
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {riskRules.map((rule) => (
          <div key={rule.key} className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 space-y-2 hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                {rule.name}
              </h3>
              <span className="font-mono font-black text-blue-400 text-sm bg-blue-500/10 px-2 py-0.5 rounded">
                {rule.value}
              </span>
            </div>
            <p className="text-xs text-slate-300">{rule.description}</p>
            <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[10px]">
              <span className="text-slate-500 font-mono">key: {rule.key}</span>
              <span className="text-emerald-400 font-bold">{rule.status}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-[#0f172a]/80 border border-slate-800 rounded-xl p-5 space-y-3">
        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Safety Guarantee & Invariant</h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          The <strong className="text-slate-200">RiskManager</strong> acts as a strict decision gateway between strategy signals and order execution handlers.
          It returns structured decisions (<code className="text-emerald-400">APPROVED</code> or <code className="text-rose-400">REJECTED</code>) with human-readable rejection reasons.
          The RiskManager <strong className="text-slate-200">never executes orders or accesses external exchange APIs directly</strong>.
        </p>
      </div>
    </div>
  );
}
