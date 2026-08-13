import { SystemStatus, StrategyInfo, BacktestResult, PortfolioState } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `API error: ${res.status}`);
  }

  return res.json();
}

export const api = {
  getSystemStatus: () => fetchJson<SystemStatus>('/system/status'),
  getStrategies: () => fetchJson<StrategyInfo[]>('/strategies'),
  getBacktests: () => fetchJson<BacktestResult[]>('/backtests'),
  getBacktestById: (id: number) => fetchJson<BacktestResult>(`/backtests/${id}`),
  runBacktest: (data: any) =>
    fetchJson<BacktestResult>('/backtests', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getPortfolio: (sessionType = 'PAPER') =>
    fetchJson<PortfolioState>(`/portfolio?session_type=${sessionType}`),
};
