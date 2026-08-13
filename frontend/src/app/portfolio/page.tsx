export default function PortfolioPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Portfolio</h1>
        <p className="text-slate-400 mt-1">Track allocations, equity curves, and position history.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-sm text-slate-400">Cash Balance</div>
          <div className="text-2xl font-bold mt-1">$10,000.00 USDT</div>
        </div>
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-sm text-slate-400">Unrealized PnL</div>
          <div className="text-2xl font-bold mt-1">$0.00</div>
        </div>
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-sm text-slate-400">Realized PnL</div>
          <div className="text-2xl font-bold mt-1">$0.00</div>
        </div>
      </div>
    </div>
  );
}
