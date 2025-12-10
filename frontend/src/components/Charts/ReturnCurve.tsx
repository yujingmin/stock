/**
 * 收益曲线图组件
 */
import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { Card, Spin } from 'antd';

interface ReturnData {
  date: string;
  return: number;
  cumulative_return: number;
  benchmark_return?: number;
}

interface ReturnCurveProps {
  title: string;
  data: ReturnData[];
  loading?: boolean;
  showBenchmark?: boolean;
}

const ReturnCurve: React.FC<ReturnCurveProps> = ({
  title,
  data,
  loading = false,
  showBenchmark = false,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current || !data || data.length === 0) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }

    // 准备数据
    const dates = data.map((item) => item.date);
    const returns = data.map((item) => (item.cumulative_return * 100).toFixed(2));
    const benchmarkReturns = showBenchmark
      ? data.map((item) => ((item.benchmark_return || 0) * 100).toFixed(2))
      : [];

    // 配置图表
    const option: echarts.EChartsOption = {
      title: {
        text: '累计收益率',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        formatter: (params: any) => {
          let result = `${params[0].axisValue}<br/>`;
          params.forEach((item: any) => {
            result += `${item.marker} ${item.seriesName}: ${item.value}%<br/>`;
          });
          return result;
        },
      },
      legend: {
        data: showBenchmark ? ['策略收益', '基准收益'] : ['策略收益'],
        top: 30,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}%',
        },
        splitLine: {
          show: true,
        },
      },
      series: [
        {
          name: '策略收益',
          type: 'line',
          data: returns,
          smooth: true,
          lineStyle: {
            width: 2,
            color: '#1890ff',
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' },
            ]),
          },
        },
        ...(showBenchmark
          ? [
              {
                name: '基准收益',
                type: 'line',
                data: benchmarkReturns,
                smooth: true,
                lineStyle: {
                  width: 2,
                  color: '#52c41a',
                  type: 'dashed' as const,
                },
              },
            ]
          : []),
      ],
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100,
        },
        {
          start: 0,
          end: 100,
        },
      ],
    };

    chartInstance.current.setOption(option);

    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data, showBenchmark]);

  return (
    <Card title={title}>
      <Spin spinning={loading}>
        <div ref={chartRef} style={{ width: '100%', height: '400px' }} />
      </Spin>
    </Card>
  );
};

export default ReturnCurve;
