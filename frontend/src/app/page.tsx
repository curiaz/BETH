import Link from 'next/link';

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Trading Dashboard</h1>
        <p className="text-slate-400 mt-1">
          Monitor algorithmic trading strategies for BTC/USDT and ETH/USDT.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-sm font-medium text-slate-400">Total Equity</div>
          <div className="text-2xl font-bold mt-2">$10,000.00</div>
          <div className="text-xs text-emerald-400 mt-1">Initial Balance</div>
        </div>

        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-sm font-medium text-slate-400">Active Mode</div>
          <div className="text-2xl font-bold mt-2 text-emerald-400">Paper</div>
          <div className="text-xs text-slate-500 mt-1">Simulated execution</div>
        </div>

        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-sm font-medium text-slate-400">Supported Assets</div>
          <div className="text-2xl font-bold mt-2">BTC, ETH</div>
          <div className="text-xs text-slate-500 mt-1">Binance Market Data</div>
        </div>

        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-sm font-medium text-slate-400">Registered Strategies</div>
          <div className="text-2xl font-bold mt-2">2</div>
          <div className="text-xs text-blue-400 mt-1">SMA Cross, RSI Reversion</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h2 className="text-lg font-semibold">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-4">
            <Link
              href="/backtests"
              className="p-4 rounded-lg bg-blue-600/10 hover:bg-blue-600/20 border border-blue-500/20 text-blue-400 font-medium text-center transition-colors"
            >
              Run Backtest
            </Link>
            <Link
              href="/paper-trading"
              className="p-4 rounded-lg bg-emerald-600/10 hover:bg-emerald-600/20 border border-emerald-500/20 text-emerald-400 font-medium text-center transition-colors"
            >
              Paper Trading Session
            </Link>
          </div>
        </div>

        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h2 className="text-lg font-semibold">Risk Management Constraints</h2>
          <ul className="text-sm space-y-2 text-slate-300">
            <li className="flex justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Max Position Size</span>
              <span className="font-mono">20% of Equity</span>
            </li>
            <li className="flex justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Max Drawdown Limit</span>
              <span className="font-mono text-rose-400">15% Halt</span>
            </li>
            <li className="flex justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Max Daily Loss</span>
              <span className="font-mono text-amber-400">3% Halt</span>
            </li>
            <li className="flex justify-between">
              <span className="text-slate-400">Max Total Exposure</span>
              <span className="font-mono">80% of Equity</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
