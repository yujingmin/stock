/**
 * 策略对话页面
 */
import React, { useState, useEffect } from 'react';
import {
  Layout,
  List,
  Card,
  Button,
  Input,
  Modal,
  Form,
  Tag,
  Space,
  message,
  Spin,
  Empty,
} from 'antd';
import {
  PlusOutlined,
  MessageOutlined,
  CodeOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { conversationApi, messageApi, backtestApi, type Conversation, type Message, type BacktestResult } from '../../api/services/strategy';
import ChatPanel from './components/ChatPanel';
import CodePreview from './components/CodePreview';
import './index.css';

const { Sider, Content } = Layout;

const Strategy: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [backtestModalVisible, setBacktestModalVisible] = useState(false);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [form] = Form.useForm();

  // 加载对话列表
  const loadConversations = async () => {
    setLoading(true);
    try {
      const { conversations: data } = await conversationApi.list({
        status: 'active',
        limit: 50,
      });
      setConversations(data);
    } catch (error) {
      message.error('加载对话列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载消息列表
  const loadMessages = async (conversationId: string) => {
    setMessagesLoading(true);
    try {
      const { messages: data } = await messageApi.list(conversationId, {
        limit: 100,
      });
      setMessages(data);
    } catch (error) {
      message.error('加载消息失败');
    } finally {
      setMessagesLoading(false);
    }
  };

  // 创建新对话
  const handleCreateConversation = async (values: any) => {
    try {
      const { conversation_id } = await conversationApi.create(values);
      message.success('对话创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      await loadConversations();

      // 自动选择新创建的对话
      const newConv = conversations.find((c) => c.id === conversation_id);
      if (newConv) {
        setSelectedConversation(newConv);
        await loadMessages(conversation_id);
      }
    } catch (error) {
      message.error('创建对话失败');
    }
  };

  // 选择对话
  const handleSelectConversation = async (conversation: Conversation) => {
    setSelectedConversation(conversation);
    await loadMessages(conversation.id);
  };

  // 发送消息
  const handleSendMessage = async (content: string) => {
    if (!selectedConversation) return;

    setMessagesLoading(true);
    try {
      // 直接添加消息，后端会自动生成策略代码
      await messageApi.add(selectedConversation.id, { content });

      // 重新加载消息列表以获取 AI 回复
      await loadMessages(selectedConversation.id);

      message.success('消息发送成功');
    } catch (error: any) {
      console.error('Send message error:', error);
      message.error(error.response?.data?.detail || '发送消息失败');
    } finally {
      setMessagesLoading(false);
    }
  };

  // 运行回测
  const handleRunBacktest = async (strategyVersionId: string, code: string) => {
    setBacktestLoading(true);
    setBacktestModalVisible(true);
    setBacktestResult(null);

    try {
      const result = await backtestApi.run({
        strategy_id: strategyVersionId,
        symbol: '000001',
        initial_cash: 100000,
      });

      setBacktestResult(result);
      message.success('回测完成');
    } catch (error: any) {
      console.error('Backtest error:', error);
      message.error(error.response?.data?.detail || '回测失败');
      setBacktestModalVisible(false);
    } finally {
      setBacktestLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  return (
    <Layout className="strategy-page">
      <Sider width={300} className="conversation-list-sider" theme="light">
        <div className="sider-header">
          <h3>
            <MessageOutlined /> 策略对话
          </h3>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            新建对话
          </Button>
        </div>

        <Spin spinning={loading}>
          {conversations.length === 0 ? (
            <Empty description="暂无对话" />
          ) : (
            <List
              className="conversation-list"
              dataSource={conversations}
              renderItem={(conversation) => (
                <List.Item
                  className={selectedConversation?.id === conversation.id ? 'selected' : ''}
                  onClick={() => handleSelectConversation(conversation)}
                  style={{ cursor: 'pointer', padding: '12px 16px' }}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        {conversation.title}
                        {conversation.tags.map((tag) => (
                          <Tag key={tag} color="blue">
                            {tag}
                          </Tag>
                        ))}
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={0}>
                        <span>{conversation.description}</span>
                        <span style={{ fontSize: '12px', color: '#999' }}>
                          {conversation.message_count} 条消息 · {conversation.version_count} 个版本
                        </span>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </Spin>
      </Sider>

      <Content className="conversation-content">
        {selectedConversation ? (
          <ChatPanel
            conversation={selectedConversation}
            messages={messages}
            loading={messagesLoading}
            onSendMessage={handleSendMessage}
            onRefresh={() => loadMessages(selectedConversation.id)}
            onRunBacktest={handleRunBacktest}
          />
        ) : (
          <Empty
            description="请选择一个对话开始聊天"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            style={{ marginTop: '20%' }}
          />
        )}
      </Content>

      {/* 创建对话模态框 */}
      <Modal
        title="创建新对话"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateConversation}>
          <Form.Item
            label="对话标题"
            name="title"
            rules={[{ required: true, message: '请输入对话标题' }]}
          >
            <Input placeholder="例如：MACD金叉策略开发" />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <Input.TextArea
              rows={3}
              placeholder="简要描述这个策略的目标和思路"
            />
          </Form.Item>

          <Form.Item label="标签" name="tags">
            <Input placeholder="用逗号分隔，例如：趋势,均线,MACD" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
              <Button onClick={() => setCreateModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 回测结果模态框 */}
      <Modal
        title="回测结果"
        open={backtestModalVisible}
        onCancel={() => setBacktestModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setBacktestModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        <Spin spinning={backtestLoading}>
          {backtestResult ? (
            <div>
              <Card title="策略信息" size="small" style={{ marginBottom: '16px' }}>
                <p><strong>策略名称：</strong>{backtestResult.strategy_name}</p>
                <p><strong>股票代码：</strong>{backtestResult.symbol}</p>
                <p><strong>回测区间：</strong>{backtestResult.start_date} ~ {backtestResult.end_date}</p>
                <p><strong>初始资金：</strong>¥{backtestResult.initial_cash.toLocaleString()}</p>
              </Card>

              <Card title="绩效指标" size="small" style={{ marginBottom: '16px' }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>总收益率：</span>
                    <Tag color={backtestResult.performance.total_return >= 0 ? 'green' : 'red'}>
                      {(backtestResult.performance.total_return * 100).toFixed(2)}%
                    </Tag>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>年化收益率：</span>
                    <Tag color={backtestResult.performance.annual_return >= 0 ? 'green' : 'red'}>
                      {(backtestResult.performance.annual_return * 100).toFixed(2)}%
                    </Tag>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>夏普比率：</span>
                    <span>{backtestResult.performance.sharpe_ratio.toFixed(2)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>最大回撤：</span>
                    <Tag color="red">
                      {(backtestResult.performance.max_drawdown * 100).toFixed(2)}%
                    </Tag>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>胜率：</span>
                    <span>{(backtestResult.performance.win_rate * 100).toFixed(2)}%</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>交易次数：</span>
                    <span>{backtestResult.performance.total_trades}</span>
                  </div>
                </Space>
              </Card>

              <Card title="交易记录" size="small">
                <p>共 {backtestResult.total_trades_count} 笔交易</p>
                {backtestResult.trading_records.length > 0 && (
                  <List
                    size="small"
                    dataSource={backtestResult.trading_records.slice(0, 10)}
                    renderItem={(record: any) => (
                      <List.Item>
                        <span>{record.date}</span>
                        <Tag color={record.type === 'BUY' ? 'green' : 'red'}>
                          {record.type}
                        </Tag>
                        <span>价格: ¥{record.price}</span>
                        <span>数量: {record.size}</span>
                      </List.Item>
                    )}
                  />
                )}
              </Card>
            </div>
          ) : (
            <Empty description="正在运行回测，请稍候..." />
          )}
        </Spin>
      </Modal>
    </Layout>
  );
};

export default Strategy;
