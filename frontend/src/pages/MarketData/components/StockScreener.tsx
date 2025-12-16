import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Button,
  Table,
  Space,
  message,
  Modal,
  Select,
  Tooltip,
  Tag
} from 'antd';
import {
  SearchOutlined,
  SaveOutlined,
  DownloadOutlined,
  DeleteOutlined,
  FolderOutlined
} from '@ant-design/icons';
import { marketDataApi, type StockScreenFilter, type StockInfo, type ScreenRule } from '@/api/services/marketData';

const { Option } = Select;

const StockScreener: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<StockInfo[]>([]);
  const [savedRules, setSavedRules] = useState<ScreenRule[]>([]);
  const [saveModalVisible, setSaveModalVisible] = useState(false);
  const [currentFilter, setCurrentFilter] = useState<StockScreenFilter>({});

  // 加载已保存的规则
  useEffect(() => {
    loadSavedRules();
  }, []);

  const loadSavedRules = async () => {
    try {
      const { rules } = await marketDataApi.getScreenRules();
      setSavedRules(rules);
    } catch (error: any) {
      console.error('加载筛选规则失败:', error);
    }
  };

  // 执行筛选
  const handleScreen = async (values: any) => {
    setLoading(true);
    try {
      // 构建筛选条件
      const filter: StockScreenFilter = {
        ...(values.max_pe && { max_pe: values.max_pe }),
        ...(values.min_dividend_yield && { min_dividend_yield: values.min_dividend_yield }),
        ...(values.max_pb && { max_pb: values.max_pb }),
        ...(values.min_market_cap && { min_market_cap: values.min_market_cap }),
        ...(values.max_market_cap && { max_market_cap: values.max_market_cap }),
        ...(values.min_price && { min_price: values.min_price }),
        ...(values.max_price && { max_price: values.max_price }),
      };

      setCurrentFilter(filter);

      const result = await marketDataApi.screenStocks(filter);
      setResults(result.results);
      message.success(`找到 ${result.count} 只符合条件的股票`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '筛选失败');
    } finally {
      setLoading(false);
    }
  };

  // 保存筛选规则
  const handleSaveRule = async (values: { name: string; description?: string }) => {
    try {
      await marketDataApi.saveScreenRule(values.name, currentFilter, values.description);
      message.success('筛选规则已保存');
      setSaveModalVisible(false);
      loadSavedRules();
    } catch (error: any) {
      message.error('保存失败');
    }
  };

  // 应用已保存的规则
  const handleApplyRule = async (ruleId: string) => {
    setLoading(true);
    try {
      const result = await marketDataApi.applyScreenRule(ruleId);
      setResults(result.results);
      setCurrentFilter(result.conditions);

      // 更新表单显示
      form.setFieldsValue(result.conditions);

      message.success(`应用规则 "${result.rule_name}" 成功，找到 ${result.count} 只股票`);
    } catch (error: any) {
      message.error('应用规则失败');
    } finally {
      setLoading(false);
    }
  };

  // 删除规则
  const handleDeleteRule = async (ruleId: string) => {
    try {
      await marketDataApi.deleteScreenRule(ruleId);
      message.success('规则已删除');
      loadSavedRules();
    } catch (error: any) {
      message.error('删除失败');
    }
  };

  // 导出结果
  const handleExport = (format: 'csv' | 'excel') => {
    if (Object.keys(currentFilter).length === 0) {
      message.warning('请先执行筛选');
      return;
    }

    const url = marketDataApi.exportScreenResults(currentFilter, format);
    window.open(url, '_blank');
    message.success('开始下载');
  };

  // 表格列定义
  const columns = [
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
      fixed: 'left' as const,
    },
    {
      title: '股票名称',
      dataIndex: 'name',
      key: 'name',
      width: 120,
      fixed: 'left' as const,
    },
    {
      title: '当前价格',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '涨跌幅',
      dataIndex: 'change_pct',
      key: 'change_pct',
      width: 100,
      render: (pct: number) => (
        <Tag color={pct >= 0 ? 'red' : 'green'}>
          {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
        </Tag>
      ),
    },
    {
      title: '市盈率',
      dataIndex: 'pe_ratio',
      key: 'pe_ratio',
      width: 100,
      render: (pe: number) => pe ? pe.toFixed(2) : '-',
    },
    {
      title: '市净率',
      dataIndex: 'pb_ratio',
      key: 'pb_ratio',
      width: 100,
      render: (pb: number) => pb ? pb.toFixed(2) : '-',
    },
    {
      title: '股息率',
      dataIndex: 'dividend_yield',
      key: 'dividend_yield',
      width: 100,
      render: (yield_val: number) => yield_val ? `${yield_val.toFixed(2)}%` : '-',
    },
    {
      title: '市值(亿)',
      dataIndex: 'market_cap',
      key: 'market_cap',
      width: 120,
      render: (cap: number) => cap ? cap.toFixed(2) : '-',
    },
    {
      title: '所属行业',
      dataIndex: 'industry',
      key: 'industry',
      width: 120,
    },
  ];

  return (
    <div>
      {/* 筛选条件表单 */}
      <Card title="筛选条件" style={{ marginBottom: 16 }}>
        <Form
          form={form}
          layout="inline"
          onFinish={handleScreen}
        >
          <Form.Item name="max_pe" label="最大市盈率">
            <InputNumber min={0} placeholder="如：20" style={{ width: 120 }} />
          </Form.Item>

          <Form.Item name="min_dividend_yield" label="最小股息率(%)">
            <InputNumber min={0} max={100} placeholder="如：3" style={{ width: 120 }} />
          </Form.Item>

          <Form.Item name="max_pb" label="最大市净率">
            <InputNumber min={0} placeholder="如：2" style={{ width: 120 }} />
          </Form.Item>

          <Form.Item name="min_market_cap" label="最小市值(亿)">
            <InputNumber min={0} placeholder="如：100" style={{ width: 120 }} />
          </Form.Item>

          <Form.Item name="max_market_cap" label="最大市值(亿)">
            <InputNumber min={0} placeholder="如：1000" style={{ width: 120 }} />
          </Form.Item>

          <Form.Item name="min_price" label="最低价格">
            <InputNumber min={0} placeholder="如：10" style={{ width: 120 }} />
          </Form.Item>

          <Form.Item name="max_price" label="最高价格">
            <InputNumber min={0} placeholder="如：100" style={{ width: 120 }} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SearchOutlined />}
                loading={loading}
              >
                开始筛选
              </Button>

              <Button
                icon={<SaveOutlined />}
                onClick={() => setSaveModalVisible(true)}
                disabled={Object.keys(currentFilter).length === 0}
              >
                保存规则
              </Button>

              <Button onClick={() => form.resetFields()}>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {/* 已保存的规则 */}
      {savedRules.length > 0 && (
        <Card title="已保存的规则" style={{ marginBottom: 16 }}>
          <Space wrap>
            {savedRules.map((rule) => (
              <Tooltip key={rule.id} title={rule.description || '无描述'}>
                <Tag
                  icon={<FolderOutlined />}
                  color="blue"
                  style={{ cursor: 'pointer', padding: '4px 8px' }}
                  closable
                  onClose={(e) => {
                    e.preventDefault();
                    handleDeleteRule(rule.id);
                  }}
                  onClick={() => handleApplyRule(rule.id)}
                >
                  {rule.name}
                </Tag>
              </Tooltip>
            ))}
          </Space>
        </Card>
      )}

      {/* 筛选结果 */}
      <Card
        title={`筛选结果 (${results.length}只)`}
        extra={
          <Space>
            <Button
              icon={<DownloadOutlined />}
              onClick={() => handleExport('csv')}
              disabled={results.length === 0}
            >
              导出CSV
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={() => handleExport('excel')}
              disabled={results.length === 0}
            >
              导出Excel
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={results}
          rowKey="symbol"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 保存规则对话框 */}
      <Modal
        title="保存筛选规则"
        open={saveModalVisible}
        onCancel={() => setSaveModalVisible(false)}
        footer={null}
      >
        <Form layout="vertical" onFinish={handleSaveRule}>
          <Form.Item
            name="name"
            label="规则名称"
            rules={[{ required: true, message: '请输入规则名称' }]}
          >
            <Input placeholder="如：高股息低市盈率" />
          </Form.Item>

          <Form.Item name="description" label="规则描述">
            <Input.TextArea
              rows={3}
              placeholder="描述这个筛选规则的用途..."
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
              <Button onClick={() => setSaveModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default StockScreener;
