export interface SystemStatus {
  app_name: string;
  version: string;
  environment: string;
  trading_mode: string;
  exchange: string;
  supported_symbols: string[];
  default_timeframe: string;
  paper_initial_balance: number;
}

export interface StrategyParameter {
  name: string;
  type: string;
  default: any;
  min_value?: any;
  max_value?: any;
  description: string;
}

export interface StrategyInfo {
  name: string;
  version: string;
  description: string;
  parameters: StrategyParameter[];
}

export interface BacktestResult {
  id?: number;
  strategy_name: string;
  parameters: Record<string, any>;
  symbol: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_equity: number;
  total_return_pct: number;
  sharpe_ratio?: number;
  sortino_ratio?: number;
  max_drawdown_pct: number;
  win_rate: number;
  total_trades: number;
  profit_factor?: number;
  equity_curve?: Array<{ timestamp: string; equity: number }>;
  trade_log?: Array<Record<string, any>>;
  created_at?: string;
}

export interface PortfolioState {
  total_equity: number;
  cash_balance: number;
  unrealized_pnl: number;
  realized_pnl: number;
  positions: Array<{
    asset_id: number;
    side: string;
    quantity: number;
    entry_price: number;
    current_price: number;
    unrealized_pnl: number;
    status: string;
  }>;
  session_type: string;
}
