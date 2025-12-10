/**
 * 通知统计分析页面
 * 显示通知的统计图表和趋势分析
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  DatePicker,
  Select,
  Spin,
  message,
  Tag,
  Space,
} from 'antd';
import {
  BellOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import * as echarts from 'echarts';
import dayjs from 'dayjs';
import './AnalyticsPage.css';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface NotificationStats {
  period: string;
  start_date: string;
  end_date: string;
  total_notifications: number;
  urgent_count: number;
  normal_count: number;
  minor_count: number;
  type_distribution: Record<string, number>;
  pushed_count: number;
  read_count: number;
  avg_read_time: number | null;
  most_triggered_symbol: string | null;
  most_triggered_strategy: string | null;
}

const NotificationAnalytics: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<NotificationStats | null>(null);
  const [period, setPeriod] = useState('monthly');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(30, 'days'),
    dayjs(),
  ]);

  // 加载统计数据
  const loadStats = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        period,
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
      });

      const response = await fetch(`/api/v1/notification/stats?${params.toString()}`);
      if (!response.ok) {
        throw new Error('加载统计数据失败');
      }

      const data = await response.json();
      setStats(data);

      // 渲染图表
      setTimeout(() => {
        renderPriorityChart(data);
        renderTypeChart(data);
      }, 100);
    } catch (error: any) {
      message.error(error.message || '加载统计数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 渲染优先级分布图
  const renderPriorityChart = (data: NotificationStats) => {
    const chartDom = document.getElementById('priority-chart');
    if (!chartDom) return;

    const chart = echarts.init(chartDom);
    const option = {
      title: {
        text: '优先级分布',
        left: 'center',
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'vertical',
        left: 'left',
      },
      series: [
        {
          name: '优先级',
          type: 'pie',
          radius: '50%',
          data: [
            {
              value: data.urgent_count,
              name: '紧急',
              itemStyle: { color: '#ff4d4f' },
            },
            {
              value: data.normal_count,
              name: '普通',
              itemStyle: { color: '#1890ff' },
            },
            {
              value: data.minor_count,
              name: '次要',
              itemStyle: { color: '#52c41a' },
            },
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    };

    chart.setOption(option);
  };

  // 渲染类型分布图
  const renderTypeChart = (data: NotificationStats) => {
    const chartDom = document.getElementById('type-chart');
    if (!chartDom) return;

    const chart = echarts.init(chartDom);

    const typeNames: Record<string, string> = {
      risk_alert: '风控预警',
      strategy_signal: '策略信号',
      backtest_complete: '回测完成',
      data_anomaly: '数据异常',
      system_notice: '系统通知',
      position_reminder: '持仓提醒',
    };

    const chartData = Object.entries(data.type_distribution).map(([type, count]) => ({
      name: typeNames[type] || type,
      value: count,
    }));

    const option = {
      title: {
        text: '类型分布',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      xAxis: {
        type: 'category',
        data: chartData.map((item) => item.name),
        axisLabel: {
          interval: 0,
          rotate: 30,
        },
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          name: '数量',
          type: 'bar',
          data: chartData.map((item) => item.value),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#83bff6' },
              { offset: 0.5, color: '#188df0' },
              { offset: 1, color: '#188df0' },
            ]),
          },
          emphasis: {
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#2378f7' },
                { offset: 0.7, color: '#2378f7' },
                { offset: 1, color: '#83bff6' },
              ]),
            },
          },
        },
      ],
    };

    chart.setOption(option);
  };

  // 初始加载
  useEffect(() => {
    loadStats();
  }, [period, dateRange]);

  // 窗口大小变化时重绘图表
  useEffect(() => {
    const handleResize = () => {
      const priorityChart = echarts.getInstanceByDom(
        document.getElementById('priority-chart')!
      );
      const typeChart = echarts.getInstanceByDom(
        document.getElementById('type-chart')!
      );
      priorityChart?.resize();
      typeChart?.resize();
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 格式化平均阅读时间
  const formatReadTime = (seconds: number | null) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds.toFixed(0)}秒`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}分钟`;
    return `${(seconds / 3600).toFixed(1)}小时`;
  };

  return (
    <div className="notification-analytics">
      <Card
        title="通知统计分析"
        extra={
          <Space>
            <Select
              value={period}
              onChange={setPeriod}
              style={{ width: 120 }}
            >
              <Option value="daily">日报</Option>
              <Option value="weekly">周报</Option>
              <Option value="monthly">月报</Option>
            </Select>
            <RangePicker
              value={dateRange}
              onChange={(dates) => dates && setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
              format="YYYY-MM-DD"
            />
          </Space>
        }
      >
        <Spin spinning={loading}>
          {stats && (
            <>
              {/* 统计概览 */}
              <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="总通知数"
                      value={stats.total_notifications}
                      prefix={<BellOutlined />}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="紧急通知"
                      value={stats.urgent_count}
                      prefix={<WarningOutlined />}
                      valueStyle={{ color: '#ff4d4f' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="已读通知"
                      value={stats.read_count}
                      prefix={<CheckCircleOutlined />}
                      suffix={`/ ${stats.total_notifications}`}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="平均阅读时间"
                      value={formatReadTime(stats.avg_read_time)}
                      prefix={<ClockCircleOutlined />}
                    />
                  </Card>
                </Col>
              </Row>

              {/* 详细统计 */}
              <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={12}>
                  <Card>
                    <Statistic
                      title="已推送通知"
                      value={stats.pushed_count}
                      suffix={`/ ${stats.total_notifications}`}
                    />
                    <div style={{ marginTop: 8 }}>
                      推送率：
                      {stats.total_notifications > 0
                        ? ((stats.pushed_count / stats.total_notifications) * 100).toFixed(1)
                        : 0}
                      %
                    </div>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card>
                    <Statistic
                      title="阅读率"
                      value={
                        stats.total_notifications > 0
                          ? ((stats.read_count / stats.total_notifications) * 100).toFixed(1)
                          : 0
                      }
                      suffix="%"
                    />
                  </Card>
                </Col>
              </Row>

              {/* 触发统计 */}
              <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={12}>
                  <Card title="触发最多的股票">
                    {stats.most_triggered_symbol ? (
                      <Tag color="blue" style={{ fontSize: 16 }}>
                        {stats.most_triggered_symbol}
                      </Tag>
                    ) : (
                      <span style={{ color: '#999' }}>暂无数据</span>
                    )}
                  </Card>
                </Col>
                <Col span={12}>
                  <Card title="触发最多的策略">
                    {stats.most_triggered_strategy ? (
                      <Tag color="green" style={{ fontSize: 16 }}>
                        {stats.most_triggered_strategy}
                      </Tag>
                    ) : (
                      <span style={{ color: '#999' }}>暂无数据</span>
                    )}
                  </Card>
                </Col>
              </Row>

              {/* 图表 */}
              <Row gutter={16}>
                <Col span={12}>
                  <Card>
                    <div id="priority-chart" style={{ width: '100%', height: 300 }}></div>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card>
                    <div id="type-chart" style={{ width: '100%', height: 300 }}></div>
                  </Card>
                </Col>
              </Row>
            </>
          )}
        </Spin>
      </Card>
    </div>
  );
};

export default NotificationAnalytics;
