/**
 * 市场数据页面
 * 展示股票实时行情、K线图、技术指标等
 */
import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Input, Button, Space, Statistic, message, Tabs } from 'antd';
import { SearchOutlined, LineChartOutlined, HeatMapOutlined, FilterOutlined } from '@ant-design/icons';
import { KLineChart, FactorHeatmap, ReturnCurve } from '@/components/Charts';
import { getStockQuote, getStockKLine, getStockIndicators } from '@/api/services/market';
import type { StockRealtimeQuote, KLineData, StockIndicators } from '@/types/market';
import StockScreener from './components/StockScreener';
import './index.css';

const { Search } = Input;

const MarketDataPage: React.FC = () => {
  const [symbol, setSymbol] = useState<string>('000001');
  const [loading, setLoading] = useState<boolean>(false);
  const [quote, setQuote] = useState<StockRealtimeQuote | null>(null);
  const [klineData, setKlineData] = useState<KLineData[]>([]);
  const [indicators, setIndicators] = useState<StockIndicators | null>(null);
  const [period, setPeriod] = useState<string>('daily');

  // 加载股票数据
  const loadStockData = async (stockSymbol: string) => {
    setLoading(true);
    try {
      // 并行加载数据
      const [quoteData, klineResp, indicatorsData] = await Promise.all([
        getStockQuote(stockSymbol),
        getStockKLine(stockSymbol, period, undefined, undefined, true),
        getStockIndicators(stockSymbol),
      ]);

      setQuote(quoteData);
      setKlineData(klineResp.data);
      setIndicators(indicatorsData);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加载数据失败');
      console.error('加载股票数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 搜索股票
  const handleSearch = (value: string) => {
    if (!value.trim()) {
      message.warning('请输入股票代码');
      return;
    }
    setSymbol(value);
    loadStockData(value);
  };

  // 切换周期
  const handlePeriodChange = async (newPeriod: string) => {
    setPeriod(newPeriod);
    setLoading(true);
    try {
      const klineResp = await getStockKLine(symbol, newPeriod, undefined, undefined, true);
      setKlineData(klineResp.data);
    } catch (error: any) {
      message.error('加载K线数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    loadStockData(symbol);
  }, []);

  // 计算涨跌颜色
  const getPriceColor = (changePercent: number) => {
    return changePercent >= 0 ? '#ef232a' : '#14b143';
  };

  const tabItems = [
    {
      key: 'quote',
      label: (
        <span>
          <LineChartOutlined />
          行情查看
        </span>
      ),
      children: (
        <div>
          {/* 搜索栏 */}
          <Card style={{ marginBottom: 16 }}>
            <Space size="large">
              <Search
                placeholder="输入股票代码（如：000001）"
                allowClear
                enterButton={<SearchOutlined />}
                size="large"
                onSearch={handleSearch}
                style={{ width: 400 }}
                defaultValue={symbol}
              />
              <Button
                type="primary"
                icon={<LineChartOutlined />}
                size="large"
                onClick={() => loadStockData(symbol)}
                loading={loading}
              >
                刷新数据
              </Button>
            </Space>
          </Card>

          {/* 实时行情 */}
          {quote && (
            <Card title={`${quote.name} (${quote.symbol})`} style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="最新价"
                    value={quote.price}
                    precision={2}
                    valueStyle={{ color: getPriceColor(quote.change_percent) }}
                    suffix="元"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="涨跌幅"
                    value={quote.change_percent}
                    precision={2}
                    valueStyle={{ color: getPriceColor(quote.change_percent) }}
                    suffix="%"
                    prefix={quote.change_percent >= 0 ? '+' : ''}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="涨跌额"
                    value={quote.change_amount}
                    precision={2}
                    valueStyle={{ color: getPriceColor(quote.change_percent) }}
                    prefix={quote.change_amount >= 0 ? '+' : ''}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="成交量"
                    value={quote.volume}
                    suffix="手"
                  />
                </Col>
              </Row>
              <Row gutter={16} style={{ marginTop: 16 }}>
                <Col span={6}>
                  <Statistic title="今开" value={quote.open} precision={2} />
                </Col>
                <Col span={6}>
                  <Statistic title="最高" value={quote.high} precision={2} />
                </Col>
                <Col span={6}>
                  <Statistic title="最低" value={quote.low} precision={2} />
                </Col>
                <Col span={6}>
                  <Statistic title="昨收" value={quote.close_yesterday} precision={2} />
                </Col>
              </Row>
            </Card>
          )}

          {/* 股票指标 */}
          {indicators && (
            <Card title="主要指标" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="市盈率(PE)"
                    value={indicators.pe_ratio || '-'}
                    precision={2}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="市净率(PB)"
                    value={indicators.pb_ratio || '-'}
                    precision={2}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="股息率"
                    value={indicators.dividend_yield || '-'}
                    precision={2}
                    suffix="%"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="ROE"
                    value={indicators.roe || '-'}
                    precision={2}
                    suffix="%"
                  />
                </Col>
              </Row>
            </Card>
          )}

          {/* K线图 */}
          <KLineChart
            symbol={symbol}
            data={klineData}
            loading={loading}
            onPeriodChange={handlePeriodChange}
          />
        </div>
      ),
    },
    {
      key: 'screener',
      label: (
        <span>
          <FilterOutlined />
          股票筛选
        </span>
      ),
      children: <StockScreener />,
    },
  ];

  return (
    <div className="market-data-page">
      <Tabs defaultActiveKey="quote" items={tabItems} />
    </div>
  );
};

export default MarketDataPage;
