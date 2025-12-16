/**
 * 市场数据API服务
 */
import apiClient from '../client';

/**
 * 股票筛选条件接口
 */
export interface StockScreenFilter {
  max_pe?: number;              // 最大市盈率
  min_dividend_yield?: number;  // 最小股息率
  max_pb?: number;              // 最大市净率
  min_market_cap?: number;      // 最小市值（亿元）
  max_market_cap?: number;      // 最大市值（亿元）
  industries?: string[];        // 行业列表
  min_price?: number;           // 最小价格
  max_price?: number;           // 最大价格
}

/**
 * 股票基本信息接口
 */
export interface StockInfo {
  symbol: string;          // 股票代码
  name: string;            // 股票名称
  price: number;           // 当前价格
  change_pct: number;      // 涨跌幅
  volume: number;          // 成交量
  market_cap: number;      // 市值
  pe_ratio?: number;       // 市盈率
  pb_ratio?: number;       // 市净率
  dividend_yield?: number; // 股息率
  industry?: string;       // 所属行业
}

/**
 * K线数据接口
 */
export interface KLineData {
  date: string;     // 日期
  open: number;     // 开盘价
  close: number;    // 收盘价
  high: number;     // 最高价
  low: number;      // 最低价
  volume: number;   // 成交量
  amount?: number;  // 成交额
}

/**
 * 筛选规则接口
 */
export interface ScreenRule {
  id: string;
  name: string;
  description?: string;
  conditions: StockScreenFilter;
  created_at: string;
  updated_at: string;
}

/**
 * 筛选结果接口
 */
export interface ScreenResult {
  results: StockInfo[];
  count: number;
  conditions?: StockScreenFilter;
}

/**
 * 市场数据API
 */
export const marketDataApi = {
  /**
   * 筛选股票
   */
  screenStocks: async (filter: StockScreenFilter): Promise<ScreenResult> => {
    const response = await apiClient.post<ScreenResult>('/market-data/screen', filter);
    return response.data;
  },

  /**
   * 保存筛选规则
   */
  saveScreenRule: async (name: string, conditions: StockScreenFilter, description?: string) => {
    const response = await apiClient.post('/market-data/screen/rules', {
      name,
      conditions,
      description,
    });
    return response.data;
  },

  /**
   * 获取所有筛选规则
   */
  getScreenRules: async (): Promise<{ rules: ScreenRule[]; count: number }> => {
    const response = await apiClient.get('/market-data/screen/rules');
    return response.data;
  },

  /**
   * 获取筛选规则详情
   */
  getScreenRule: async (ruleId: string): Promise<ScreenRule> => {
    const response = await apiClient.get(`/market-data/screen/rules/${ruleId}`);
    return response.data;
  },

  /**
   * 应用筛选规则
   */
  applyScreenRule: async (ruleId: string): Promise<ScreenResult & { rule_name: string }> => {
    const response = await apiClient.post(`/market-data/screen/rules/${ruleId}/apply`);
    return response.data;
  },

  /**
   * 删除筛选规则
   */
  deleteScreenRule: async (ruleId: string) => {
    const response = await apiClient.delete(`/market-data/screen/rules/${ruleId}`);
    return response.data;
  },

  /**
   * 导出K线数据
   */
  exportKLineData: (
    symbol: string,
    period: 'daily' | 'weekly' | 'monthly' = 'daily',
    startDate?: string,
    endDate?: string,
    format: 'csv' | 'excel' = 'csv',
    withIndicators: boolean = false
  ): string => {
    const params = new URLSearchParams({
      period,
      format,
      with_indicators: String(withIndicators),
    });

    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    return `${apiClient.defaults.baseURL}/market-data/export/kline/${symbol}?${params.toString()}`;
  },

  /**
   * 导出筛选结果
   */
  exportScreenResults: (conditions: StockScreenFilter, format: 'csv' | 'excel' = 'csv'): string => {
    const params = new URLSearchParams({
      conditions: JSON.stringify(conditions),
      format,
    });

    return `${apiClient.defaults.baseURL}/market-data/export/screen?${params.toString()}`;
  },
};
