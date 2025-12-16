/**
 * 策略开发 API 服务
 */
import { apiClient } from '../client';

// ============ 类型定义 ============

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  status: 'active' | 'completed' | 'archived';
  current_strategy_id?: string;
  tags: string[];
  message_count: number;
  version_count: number;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  generated_code?: string;
  code_language?: string;
  strategy_version_id?: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface StrategyVersion {
  id: string;
  strategy_name: string;
  user_id: string;
  conversation_id?: string;
  message_id?: string;
  code: string;
  code_encrypted: boolean;
  version: number;
  version_description?: string;
  strategy_type?: string;
  parameters: Record<string, any>;
  backtest_result_id?: string;
  performance_metrics?: Record<string, any>;
  status: 'draft' | 'testing' | 'active' | 'archived';
  created_at: string;
}

export interface StrategyTemplate {
  id: string;
  name: string;
  description: string;
  code: string;
  strategy_type: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  risk_level: 'low' | 'medium' | 'high';
  suitable_markets: string[];
  tags: string[];
  parameters: Record<string, any>;
  usage_count: number;
  created_by: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

// ============ 对话管理 API ============

export const conversationApi = {
  /**
   * 创建策略对话
   */
  create: async (data: {
    title: string;
    description?: string;
    tags?: string[];
  }): Promise<{ conversation_id: string; message: string }> => {
    const response = await apiClient.post('/strategy/conversations', data);
    return response.data;
  },

  /**
   * 获取对话列表
   */
  list: async (params?: {
    status?: 'active' | 'completed' | 'archived';
    skip?: number;
    limit?: number;
  }): Promise<{ conversations: Conversation[]; count: number }> => {
    const response = await apiClient.get('/strategy/conversations', { params });
    return response.data;
  },

  /**
   * 获取对话详情
   */
  get: async (conversationId: string): Promise<Conversation> => {
    const response = await apiClient.get(`/strategy/conversations/${conversationId}`);
    return response.data;
  },

  /**
   * 更新对话
   */
  update: async (
    conversationId: string,
    data: {
      title?: string;
      description?: string;
      tags?: string[];
      status?: 'active' | 'completed' | 'archived';
    }
  ): Promise<{ message: string }> => {
    const response = await apiClient.put(`/strategy/conversations/${conversationId}`, data);
    return response.data;
  },

  /**
   * 删除对话
   */
  delete: async (conversationId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/strategy/conversations/${conversationId}`);
    return response.data;
  },
};

// ============ 消息管理 API ============

export const messageApi = {
  /**
   * 添加消息
   */
  add: async (
    conversationId: string,
    data: {
      content: string;
      generated_code?: string;
      strategy_version_id?: string;
    }
  ): Promise<{ message_id: string; message: string }> => {
    const response = await apiClient.post(`/strategy/conversations/${conversationId}/messages`, data);
    return response.data;
  },

  /**
   * 获取消息列表
   */
  list: async (
    conversationId: string,
    params?: {
      skip?: number;
      limit?: number;
    }
  ): Promise<{ messages: Message[]; count: number }> => {
    const response = await apiClient.get(`/strategy/conversations/${conversationId}/messages`, {
      params,
    });
    return response.data;
  },
};

// ============ 策略版本管理 API ============

export const strategyApi = {
  /**
   * 创建策略版本
   */
  create: async (data: {
    strategy_name: string;
    code: string;
    conversation_id?: string;
    message_id?: string;
    strategy_type?: string;
    parameters?: Record<string, any>;
    version_description?: string;
  }): Promise<{ strategy_id: string; message: string }> => {
    const response = await apiClient.post('/strategy/strategies', data);
    return response.data;
  },

  /**
   * 获取策略版本列表
   */
  list: async (params?: {
    strategy_name?: string;
    skip?: number;
    limit?: number;
  }): Promise<{ strategies: StrategyVersion[]; count: number }> => {
    const response = await apiClient.get('/strategy/strategies', { params });
    return response.data;
  },

  /**
   * 获取策略版本详情
   */
  get: async (strategyId: string): Promise<StrategyVersion> => {
    const response = await apiClient.get(`/strategy/strategies/${strategyId}`);
    return response.data;
  },

  /**
   * 比较策略版本
   */
  compare: async (
    strategyId: string,
    targetId: string
  ): Promise<{
    version_1: any;
    version_2: any;
    code_diff: any;
  }> => {
    const response = await apiClient.get(`/strategy/strategies/${strategyId}/compare/${targetId}`);
    return response.data;
  },
};

// ============ 策略模板 API ============

export const templateApi = {
  /**
   * 获取模板列表
   */
  list: async (params?: {
    strategy_type?: string;
    difficulty?: 'beginner' | 'intermediate' | 'advanced';
    tags?: string[];
    skip?: number;
    limit?: number;
  }): Promise<{ templates: StrategyTemplate[]; count: number }> => {
    const response = await apiClient.get('/strategy/templates', { params });
    return response.data;
  },

  /**
   * 获取模板详情
   */
  get: async (templateId: string): Promise<StrategyTemplate> => {
    const response = await apiClient.get(`/strategy/templates/${templateId}`);
    return response.data;
  },

  /**
   * 搜索模板
   */
  search: async (keyword: string): Promise<{ templates: StrategyTemplate[]; count: number }> => {
    const response = await apiClient.get(`/strategy/templates/search/${keyword}`);
    return response.data;
  },
};

// ============ 回测管理 API ============

export interface BacktestResult {
  strategy_id: string;
  strategy_name: string;
  symbol: string;
  start_date: string;
  end_date: string;
  initial_cash: number;
  backtest_params: Record<string, any>;
  performance: {
    total_return: number;
    annual_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    total_trades: number;
  };
  equity_curve: Array<{ date: string; value: number }>;
  trading_records: Array<any>;
  total_trades_count: number;
  created_at: string;
}

export const backtestApi = {
  /**
   * 运行策略回测
   */
  run: async (data: {
    strategy_id: string;
    symbol?: string;
    start_date?: string;
    end_date?: string;
    initial_cash?: number;
    backtest_params?: Record<string, any>;
  }): Promise<BacktestResult> => {
    const response = await apiClient.post('/strategy/backtest/run', data);
    return response.data;
  },

  /**
   * 快速回测（不保存策略版本）
   */
  quickRun: async (data: {
    strategy_code: string;
    symbol?: string;
    start_date?: string;
    end_date?: string;
    initial_cash?: number;
    strategy_params?: Record<string, any>;
  }): Promise<{
    performance: Record<string, any>;
    equity_curve: Array<any>;
    trading_records: Array<any>;
  }> => {
    const response = await apiClient.post('/strategy/backtest/quick', data);
    return response.data;
  },

  /**
   * 获取回测历史
   */
  getHistory: async (strategyId: string): Promise<{ backtest_results: BacktestResult[]; count: number }> => {
    const response = await apiClient.get(`/strategy/backtest/history/${strategyId}`);
    return response.data;
  },
};

