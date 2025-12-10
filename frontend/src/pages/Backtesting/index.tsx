/**
 * 回测系统页面
 * 配置并运行策略回测，查看回测结果
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  DatePicker,
  Select,
  Button,
  Space,
  Table,
  Statistic,
  Row,
  Col,
  message,
  Tag,
  Progress,
  Tabs,
} from 'antd';
import {
  PlayCircleOutlined,
  ReloadOutlined,
  LineChartOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { ReturnCurve } from '@/components/Charts';
import './index.css';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;

interface BacktestConfig {
  symbol: string;
  start_date: string;
  end_date: string;
  period: string;
  initial_cash: number;
  commission: number;
  stamp_duty: number;
  min_commission: number;
  slippage: number;
  strategy: {
    strategy_type: string;
    strategy_params: Record<string, any>;
  };
}

interface PerformanceMetrics {
  initial_value: number;
  final_value: number;
  total_return: number;
  annual_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_trades: number;
  won_trades: number;
  lost_trades: number;
  win_rate: number;
}

interface TradingRecord {
  date: string;
  action: string;
  price: number;
  size: number;
  commission: number;
  value: number;
}

interface BacktestTask {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  config: BacktestConfig;
  result?: {
    metrics: PerformanceMetrics;
    trading_records?: TradingRecord[];
  };
  error_message?: string;
  created_at: string;
  updated_at: string;
}

const BacktestingPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [currentTask, setCurrentTask] = useState<BacktestTask | null>(null);
  const [taskHistory, setTaskHistory] = useState<BacktestTask[]>([]);
  const [activeTab, setActiveTab] = useState('config');

  // 加载任务历史
  const loadTaskHistory = async () => {
    try {
      const response = await fetch('/api/v1/backtesting/tasks');
      if (response.ok) {
        const tasks = await response.json();
        setTaskHistory(tasks);
      }
    } catch (error) {
      console.error('加载任务历史失败:', error);
    }
  };

  // 轮询任务状态
  const pollTaskStatus = async (taskId: string) => {
    const maxPolls = 60; // 最多轮询60次（5分钟）
    let pollCount = 0;

    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/backtesting/task/${taskId}`);
        if (!response.ok) {
          throw new Error('查询任务失败');
        }

        const task: BacktestTask = await response.json();
        setCurrentTask(task);

        if (task.status === 'completed') {
          message.success('回测完成！');
          setLoading(false);
          setActiveTab('result');
          loadTaskHistory();
          return;
        }

        if (task.status === 'failed') {
          message.error(`回测失败: ${task.error_message}`);
          setLoading(false);
          return;
        }

        // 继续轮询
        pollCount++;
        if (pollCount < maxPolls) {
          setTimeout(poll, 5000); // 5秒后再次查询
        } else {
          message.warning('任务超时，请稍后手动查看结果');
          setLoading(false);
        }
      } catch (error: any) {
        message.error(error.message || '查询任务失败');
        setLoading(false);
      }
    };

    poll();
  };

  // 提交回测任务
  const handleSubmit = async (values: any) => {
    setLoading(true);

    try {
      const config: BacktestConfig = {
        symbol: values.symbol,
        start_date: values.dateRange[0].format('YYYY-MM-DD'),
        end_date: values.dateRange[1].format('YYYY-MM-DD'),
        period: values.period || 'daily',
        initial_cash: values.initial_cash,
        commission: values.commission / 10000, // 转换为小数
        stamp_duty: values.stamp_duty / 10000,
        min_commission: values.min_commission,
        slippage: values.slippage / 10000,
        strategy: {
          strategy_type: values.strategy_type,
          strategy_params: {
            fast_period: values.fast_period,
            slow_period: values.slow_period,
          },
        },
      };

      const response = await fetch('/api/v1/backtesting/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '提交回测任务失败');
      }

      const task: BacktestTask = await response.json();
      message.success('回测任务已提交');

      // 开始轮询任务状态
      pollTaskStatus(task.task_id);
    } catch (error: any) {
      message.error(error.message || '提交回测任务失败');
      setLoading(false);
    }
  };

  // 查看历史任务
  const viewHistoryTask = async (taskId: string) => {
    try {
      const response = await fetch(`/api/v1/backtesting/task/${taskId}`);
      if (!response.ok) {
        throw new Error('查询任务失败');
      }

      const task: BacktestTask = await response.json();
      setCurrentTask(task);
      setActiveTab('result');
    } catch (error: any) {
      message.error(error.message || '查询任务失败');
    }
  };

  // 初始加载
  useEffect(() => {
    loadTaskHistory();
  }, []);

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'default', text: '等待中' },
      running: { color: 'processing', text: '运行中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '失败' },
    };
    const { color, text } = statusMap[status] || statusMap.pending;
    return <Tag color={color}>{text}</Tag>;
  };

  // 任务历史表格列
  const historyColumns = [
    {
      title: '股票代码',
      dataIndex: ['config', 'symbol'],
      key: 'symbol',
    },
    {
      title: '策略类型',
      dataIndex: ['config', 'strategy', 'strategy_type'],
      key: 'strategy_type',
      render: (type: string) => type === 'simple_ma' ? '均线策略' : type,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '总收益率',
      key: 'return',
      render: (record: BacktestTask) => {
        if (record.result?.metrics) {
          const value = record.result.metrics.total_return * 100;
          return (
            <span style={{ color: value >= 0 ? '#ef232a' : '#14b143' }}>
              {value >= 0 ? '+' : ''}{value.toFixed(2)}%
            </span>
          );
        }
        return '-';
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      render: (record: BacktestTask) => (
        <Button
          type="link"
          size="small"
          onClick={() => viewHistoryTask(record.task_id)}
          disabled={record.status !== 'completed'}
        >
          查看结果
        </Button>
      ),
    },
  ];

  return (
    <div className="backtesting-page">
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 回测配置 */}
        <TabPane tab="回测配置" key="config" icon={<PlayCircleOutlined />}>
          <Card>
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
              initialValues={{
                period: 'daily',
                initial_cash: 100000,
                commission: 3,
                stamp_duty: 10,
                min_commission: 5,
                slippage: 1,
                strategy_type: 'simple_ma',
                fast_period: 5,
                slow_period: 20,
              }}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="股票代码"
                    name="symbol"
                    rules={[{ required: true, message: '请输入股票代码' }]}
                  >
                    <Input placeholder="如：000001" size="large" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="回测日期范围"
                    name="dateRange"
                    rules={[{ required: true, message: '请选择日期范围' }]}
                  >
                    <RangePicker
                      style={{ width: '100%' }}
                      size="large"
                      format="YYYY-MM-DD"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item label="K线周期" name="period">
                    <Select size="large">
                      <Option value="daily">日线</Option>
                      <Option value="weekly">周线</Option>
                      <Option value="monthly">月线</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="初始资金（元）" name="initial_cash">
                    <InputNumber
                      style={{ width: '100%' }}
                      size="large"
                      min={1000}
                      formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item label="策略类型" name="strategy_type">
                    <Select size="large">
                      <Option value="simple_ma">均线策略</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={6}>
                  <Form.Item label="佣金费率（万分之）" name="commission">
                    <InputNumber style={{ width: '100%' }} size="large" min={0} max={100} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label="印花税（万分之）" name="stamp_duty">
                    <InputNumber style={{ width: '100%' }} size="large" min={0} max={100} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label="最低佣金（元）" name="min_commission">
                    <InputNumber style={{ width: '100%' }} size="large" min={0} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label="滑点（万分之）" name="slippage">
                    <InputNumber style={{ width: '100%' }} size="large" min={0} max={100} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="快速均线周期" name="fast_period">
                    <InputNumber style={{ width: '100%' }} size="large" min={1} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="慢速均线周期" name="slow_period">
                    <InputNumber style={{ width: '100%' }} size="large" min={1} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Space size="large">
                  <Button
                    type="primary"
                    htmlType="submit"
                    size="large"
                    icon={<PlayCircleOutlined />}
                    loading={loading}
                  >
                    开始回测
                  </Button>
                  <Button
                    size="large"
                    icon={<ReloadOutlined />}
                    onClick={() => form.resetFields()}
                  >
                    重置
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* 回测结果 */}
        <TabPane tab="回测结果" key="result" icon={<LineChartOutlined />}>
          {currentTask?.result?.metrics ? (
            <>
              <Card title="绩效概览" style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  <Col span={6}>
                    <Statistic
                      title="总收益率"
                      value={currentTask.result.metrics.total_return * 100}
                      precision={2}
                      suffix="%"
                      valueStyle={{
                        color: currentTask.result.metrics.total_return >= 0 ? '#ef232a' : '#14b143',
                      }}
                      prefix={currentTask.result.metrics.total_return >= 0 ? '+' : ''}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="年化收益率"
                      value={currentTask.result.metrics.annual_return * 100}
                      precision={2}
                      suffix="%"
                      valueStyle={{
                        color: currentTask.result.metrics.annual_return >= 0 ? '#ef232a' : '#14b143',
                      }}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="夏普比率"
                      value={currentTask.result.metrics.sharpe_ratio}
                      precision={2}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="最大回撤"
                      value={currentTask.result.metrics.max_drawdown * 100}
                      precision={2}
                      suffix="%"
                      valueStyle={{ color: '#14b143' }}
                    />
                  </Col>
                </Row>

                <Row gutter={16} style={{ marginTop: 16 }}>
                  <Col span={6}>
                    <Statistic
                      title="初始资金"
                      value={currentTask.result.metrics.initial_value}
                      precision={2}
                      suffix="元"
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="最终资金"
                      value={currentTask.result.metrics.final_value}
                      precision={2}
                      suffix="元"
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="总交易次数"
                      value={currentTask.result.metrics.total_trades}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="胜率"
                      value={currentTask.result.metrics.win_rate * 100}
                      precision={2}
                      suffix="%"
                    />
                  </Col>
                </Row>
              </Card>

              <Card title="交易统计">
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="盈利交易"
                      value={currentTask.result.metrics.won_trades}
                      valueStyle={{ color: '#ef232a' }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="亏损交易"
                      value={currentTask.result.metrics.lost_trades}
                      valueStyle={{ color: '#14b143' }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="盈亏比"
                      value={
                        currentTask.result.metrics.lost_trades > 0
                          ? currentTask.result.metrics.won_trades / currentTask.result.metrics.lost_trades
                          : currentTask.result.metrics.won_trades
                      }
                      precision={2}
                    />
                  </Col>
                </Row>
              </Card>

              {/* 交易记录表格 */}
              {currentTask.result.trading_records && currentTask.result.trading_records.length > 0 && (
                <Card title="交易明细" style={{ marginTop: 16 }}>
                  <Table
                    dataSource={currentTask.result.trading_records}
                    rowKey={(record, index) => `${record.date}-${index}`}
                    pagination={{ pageSize: 10 }}
                    columns={[
                      {
                        title: '日期',
                        dataIndex: 'date',
                        key: 'date',
                      },
                      {
                        title: '操作',
                        dataIndex: 'action',
                        key: 'action',
                        render: (action: string) => (
                          <Tag color={action === 'buy' ? 'red' : 'green'}>
                            {action === 'buy' ? '买入' : '卖出'}
                          </Tag>
                        ),
                      },
                      {
                        title: '价格',
                        dataIndex: 'price',
                        key: 'price',
                        render: (price: number) => `¥${price.toFixed(2)}`,
                      },
                      {
                        title: '数量',
                        dataIndex: 'size',
                        key: 'size',
                        render: (size: number) => `${size} 股`,
                      },
                      {
                        title: '交易金额',
                        dataIndex: 'value',
                        key: 'value',
                        render: (value: number) => `¥${value.toFixed(2)}`,
                      },
                      {
                        title: '佣金',
                        dataIndex: 'commission',
                        key: 'commission',
                        render: (commission: number) => `¥${commission.toFixed(2)}`,
                      },
                    ]}
                  />
                </Card>
              )}
            </>
          ) : (
            <Card>
              <p style={{ textAlign: 'center', color: '#999', padding: '40px 0' }}>
                {loading ? '回测运行中，请稍候...' : '暂无回测结果'}
              </p>
              {loading && (
                <Progress
                  percent={100}
                  status="active"
                  showInfo={false}
                  style={{ maxWidth: 400, margin: '0 auto' }}
                />
              )}
            </Card>
          )}
        </TabPane>

        {/* 历史记录 */}
        <TabPane tab="历史记录" key="history" icon={<HistoryOutlined />}>
          <Card>
            <Table
              columns={historyColumns}
              dataSource={taskHistory}
              rowKey="task_id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default BacktestingPage;
