/**
 * K线图组件
 * 支持技术指标叠加和周期切换
 */
import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Spin, Select, Space, Switch, Card } from 'antd';
import type { KLineData } from '@/types/market';

interface KLineChartProps {
  symbol: string;
  data: KLineData[];
  loading?: boolean;
  onPeriodChange?: (period: string) => void;
}

const KLineChart: React.FC<KLineChartProps> = ({
  symbol,
  data,
  loading = false,
  onPeriodChange,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [period, setPeriod] = useState<string>('daily');
  const [showMA, setShowMA] = useState<boolean>(true);
  const [showVolume, setShowVolume] = useState<boolean>(true);

  useEffect(() => {
    if (!chartRef.current || !data || data.length === 0) return;

    // 初始化图表
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }

    // 准备数据
    const dates = data.map((item) => item.date);
    const klineData = data.map((item) => [item.open, item.close, item.low, item.high]);
    const volumes = data.map((item) => item.volume);

    // 计算均线数据
    const calculateMA = (dayCount: number) => {
      const result = [];
      for (let i = 0; i < data.length; i++) {
        if (i < dayCount - 1) {
          result.push('-');
          continue;
        }
        let sum = 0;
        for (let j = 0; j < dayCount; j++) {
          sum += data[i - j].close;
        }
        result.push((sum / dayCount).toFixed(2));
      }
      return result;
    };

    const ma5Data = showMA ? calculateMA(5) : [];
    const ma10Data = showMA ? calculateMA(10) : [];
    const ma20Data = showMA ? calculateMA(20) : [];
    const ma60Data = showMA ? calculateMA(60) : [];

    // 配置图表选项
    const option: echarts.EChartsOption = {
      animation: false,
      legend: {
        top: 10,
        left: 'center',
        data: ['K线', 'MA5', 'MA10', 'MA20', 'MA60'],
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        borderWidth: 1,
        borderColor: '#ccc',
        padding: 10,
        textStyle: {
          color: '#000',
        },
      },
      axisPointer: {
        link: [{ xAxisIndex: 'all' }],
        label: {
          backgroundColor: '#777',
        },
      },
      grid: [
        {
          left: '10%',
          right: '8%',
          top: '15%',
          height: showVolume ? '50%' : '70%',
        },
        {
          left: '10%',
          right: '8%',
          top: '70%',
          height: '15%',
        },
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
        {
          type: 'category',
          gridIndex: 1,
          data: dates,
          boundaryGap: false,
          axisLine: { onZero: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
      ],
      yAxis: [
        {
          scale: true,
          splitArea: {
            show: true,
          },
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false },
        },
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 80,
          end: 100,
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          top: '90%',
          start: 80,
          end: 100,
        },
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: klineData,
          itemStyle: {
            color: '#ef232a',
            color0: '#14b143',
            borderColor: '#ef232a',
            borderColor0: '#14b143',
          },
        },
        ...(showMA
          ? [
              {
                name: 'MA5',
                type: 'line',
                data: ma5Data,
                smooth: true,
                lineStyle: { width: 1 },
                showSymbol: false,
              },
              {
                name: 'MA10',
                type: 'line',
                data: ma10Data,
                smooth: true,
                lineStyle: { width: 1 },
                showSymbol: false,
              },
              {
                name: 'MA20',
                type: 'line',
                data: ma20Data,
                smooth: true,
                lineStyle: { width: 1 },
                showSymbol: false,
              },
              {
                name: 'MA60',
                type: 'line',
                data: ma60Data,
                smooth: true,
                lineStyle: { width: 1 },
                showSymbol: false,
              },
            ]
          : []),
        ...(showVolume
          ? [
              {
                name: '成交量',
                type: 'bar',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: volumes,
                itemStyle: {
                  color: (params: any) => {
                    const dataIndex = params.dataIndex;
                    return data[dataIndex].close >= data[dataIndex].open
                      ? '#ef232a'
                      : '#14b143';
                  },
                },
              },
            ]
          : []),
      ],
    };

    chartInstance.current.setOption(option);

    // 响应式调整
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data, showMA, showVolume]);

  const handlePeriodChange = (value: string) => {
    setPeriod(value);
    onPeriodChange?.(value);
  };

  return (
    <Card
      title={`${symbol} K线图`}
      extra={
        <Space>
          <Select
            value={period}
            onChange={handlePeriodChange}
            style={{ width: 100 }}
            options={[
              { label: '日K', value: 'daily' },
              { label: '周K', value: 'weekly' },
              { label: '月K', value: 'monthly' },
            ]}
          />
          <span>均线:</span>
          <Switch checked={showMA} onChange={setShowMA} size="small" />
          <span>成交量:</span>
          <Switch checked={showVolume} onChange={setShowVolume} size="small" />
        </Space>
      }
    >
      <Spin spinning={loading}>
        <div ref={chartRef} style={{ width: '100%', height: '600px' }} />
      </Spin>
    </Card>
  );
};

export default KLineChart;
