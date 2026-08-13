export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
        <p className="text-slate-400 mt-1">View system configuration and risk parameters.</p>
      </div>

      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
        <h2 className="text-lg font-semibold">Environment Settings</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-slate-500">Trading Mode:</span> paper</div>
          <div><span className="text-slate-500">Exchange Adapter:</span> binance</div>
          <div><span className="text-slate-500">Initial Balance:</span> $10,000 USDT</div>
          <div><span className="text-slate-500">Supported Assets:</span> BTC/USDT, ETH/USDT</div>
        </div>
      </div>
    </div>
  );
}
