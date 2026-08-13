export default function PaperTradingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Paper Trading</h1>
        <p className="text-slate-400 mt-1">Live market data simulation without real money.</p>
      </div>

      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Session Status: Idle</h2>
          <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded">
            PAPER_INITIAL_BALANCE = $10,000 USDT
          </span>
        </div>
        <p className="text-sm text-slate-400">
          Paper trading connects to live Binance tickers and simulates execution against virtual balance.
        </p>
      </div>
    </div>
  );
}
