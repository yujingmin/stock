/**
 * 市场数据 API 服务
 */
import apiClient from '../client';
import type {
  StockRealtimeQuote,
  KLineResponse,
  StockIndicators,
  ScreenFilter,
  ScreenResult,
} from '@/types/market';

/**
 * 获取股票实时行情
 */
export const getStockQuote = async (symbol: string): Promise<StockRealtimeQuote> => {
  const response = await apiClient.get(`/market-data/quote/${symbol}`);
  return response.data;
};

/**
 * 获取股票K线数据
 */
export const getStockKLine = async (
  symbol: string,
  period: string = 'daily',
  startDate?: string,
  endDate?: string,
  withIndicators: boolean = false
): Promise<KLineResponse> => {
  const params = new URLSearchParams({
    period,
    ...(startDate && { start_date: startDate }),
    ...(endDate && { end_date: endDate }),
    with_indicators: String(withIndicators),
  });

  const response = await apiClient.get(`/market-data/kline/${symbol}?${params}`);
  return response.data;
};

/**
 * 获取股票指标
 */
export const getStockIndicators = async (symbol: string): Promise<StockIndicators> => {
  const response = await apiClient.get(`/market-data/indicators/${symbol}`);
  return response.data;
};

/**
 * 筛选股票
 */
export const screenStocks = async (
  filter: ScreenFilter
): Promise<{ results: ScreenResult[]; count: number }> => {
  const response = await apiClient.post('/market-data/screen', filter);
  return response.data;
};

/**
 * 获取股票列表
 */
export const getStockList = async (): Promise<Array<{ symbol: string; name: string; market: string }>> => {
  const response = await apiClient.get('/market-data/list');
  return response.data;
};

/**
 * 同步历史数据
 */
export const syncHistoricalData = async (
  symbol: string,
  period: string = 'daily',
  years: number = 10
): Promise<any> => {
  const response = await apiClient.post(`/market-data/sync/${symbol}`, null, {
    params: { period, years },
  });
  return response.data;
};
