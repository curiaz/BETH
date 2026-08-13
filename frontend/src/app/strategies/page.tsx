export default function StrategiesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Trading Strategies</h1>
        <p className="text-slate-400 mt-1">Available strategy implementations and parameters.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">SMA Crossover</h2>
            <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded">
              v1.0.0
            </span>
          </div>
          <p className="text-sm text-slate-400">
            Simple Moving Average Crossover — buys on golden cross (fast SMA &gt; slow SMA), sells on death cross.
          </p>
          <div className="border-t border-slate-800 pt-3 text-xs space-y-1 text-slate-300">
            <div><span className="text-slate-500">Parameters:</span> fast_period (default: 20), slow_period (default: 50)</div>
          </div>
        </div>

        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">RSI Mean Reversion</h2>
            <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded">
              v1.0.0
            </span>
          </div>
          <p className="text-sm text-slate-400">
            RSI Mean Reversion — buys oversold conditions (RSI &lt; 30), sells overbought conditions (RSI &gt; 70).
          </p>
          <div className="border-t border-slate-800 pt-3 text-xs space-y-1 text-slate-300">
            <div><span className="text-slate-500">Parameters:</span> rsi_period (14), oversold (30), overbought (70)</div>
          </div>
        </div>
      </div>
    </div>
  );
}
