/**
 * 因子分布热力图组件
 */
import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { Card, Spin } from 'antd';

interface HeatmapData {
  symbol: string;
  name: string;
  value: number;
}

interface FactorHeatmapProps {
  title: string;
  data: HeatmapData[];
  loading?: boolean;
  factorName?: string;
}

const FactorHeatmap: React.FC<FactorHeatmapProps> = ({
  title,
  data,
  loading = false,
  factorName = '因子值',
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current || !data || data.length === 0) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }

    // 准备数据
    const chartData = data.map((item) => ({
      name: `${item.name}\n(${item.symbol})`,
      value: item.value,
    }));

    // 配置图表
    const option: echarts.EChartsOption = {
      title: {
        text: factorName,
        left: 'center',
      },
      tooltip: {
        formatter: (params: any) => {
          return `${params.name}<br/>${factorName}: ${params.value.toFixed(2)}`;
        },
      },
      series: [
        {
          type: 'treemap',
          data: chartData,
          roam: false,
          label: {
            show: true,
            formatter: '{b}\n{c}',
          },
          itemStyle: {
            borderColor: '#fff',
          },
          levels: [
            {
              itemStyle: {
                borderWidth: 0,
                gapWidth: 5,
              },
            },
            {
              itemStyle: {
                gapWidth: 1,
              },
            },
          ],
          visualMap: {
            type: 'continuous',
            min: Math.min(...data.map((d) => d.value)),
            max: Math.max(...data.map((d) => d.value)),
            inRange: {
              color: ['#2E7D32', '#66BB6A', '#FDD835', '#FFA726', '#EF5350'],
            },
          },
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
  }, [data, factorName]);

  return (
    <Card title={title}>
      <Spin spinning={loading}>
        <div ref={chartRef} style={{ width: '100%', height: '500px' }} />
      </Spin>
    </Card>
  );
};

export default FactorHeatmap;
