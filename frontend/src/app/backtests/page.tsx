export default function BacktestsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Backtesting</h1>
        <p className="text-slate-400 mt-1">Simulate strategies against historical market data with realistic slippage and fees.</p>
      </div>

      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
        <h2 className="text-lg font-semibold">Launch New Backtest</h2>
        <p className="text-sm text-slate-400">
          Configure a backtest using historical OHLCV data for BTC/USDT or ETH/USDT.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="p-3 bg-slate-950 rounded border border-slate-800">
            <span className="text-slate-500 text-xs block">Asset</span>
            <span className="font-semibold">BTC/USDT</span>
          </div>
          <div className="p-3 bg-slate-950 rounded border border-slate-800">
            <span className="text-slate-500 text-xs block">Strategy</span>
            <span className="font-semibold">sma_crossover</span>
          </div>
          <div className="p-3 bg-slate-950 rounded border border-slate-800">
            <span className="text-slate-500 text-xs block">Starting Capital</span>
            <span className="font-semibold">$10,000 USDT</span>
          </div>
        </div>
      </div>
    </div>
  );
}
