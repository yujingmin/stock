/**
 * 市场数据类型定义
 */

export interface StockRealtimeQuote {
  symbol: string;
  name: string;
  price: number;
  change_percent: number;
  change_amount: number;
  volume: number;
  amount: number;
  high: number;
  low: number;
  open: number;
  close_yesterday: number;
  timestamp: string;
}

export interface KLineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount?: number;
  change_percent?: number;
}

export interface KLineResponse {
  symbol: string;
  period: string;
  data: KLineData[];
  count: number;
}

export interface StockIndicators {
  symbol: string;
  pe_ratio?: number;
  pb_ratio?: number;
  dividend_yield?: number;
  roe?: number;
  total_market_cap?: number;
  circulating_market_cap?: number;
}

export interface TechnicalIndicators {
  ma5?: number;
  ma10?: number;
  ma20?: number;
  ma60?: number;
  macd?: number;
  macd_signal?: number;
  macd_hist?: number;
  k?: number;
  d?: number;
  j?: number;
  rsi14?: number;
  boll_upper?: number;
  boll_middle?: number;
  boll_lower?: number;
}

export interface ScreenFilter {
  min_pe?: number;
  max_pe?: number;
  min_pb?: number;
  max_pb?: number;
  min_dividend_yield?: number;
  min_market_cap?: number;
  max_market_cap?: number;
}

export interface ScreenResult {
  symbol: string;
  name: string;
  pe_ratio?: number;
  pb_ratio?: number;
  dividend_yield?: number;
  market_cap?: number;
}
