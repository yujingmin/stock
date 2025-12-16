/**
 * 对话面板组件
 */
import React, { useState, useRef, useEffect } from 'react';
import { Card, Input, Button, List, Avatar, Space, Tag, Spin } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, ReloadOutlined, ThunderboltOutlined } from '@ant-design/icons';
import type { Conversation, Message } from '../../../api/services/strategy';
import './ChatPanel.css';

interface ChatPanelProps {
  conversation: Conversation;
  messages: Message[];
  loading: boolean;
  onSendMessage: (content: string) => void;
  onRefresh: () => void;
  onRunBacktest?: (strategyVersionId: string, code: string) => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  conversation,
  messages,
  loading,
  onSendMessage,
  onRefresh,
  onRunBacktest,
}) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim()) return;
    onSendMessage(inputValue);
    setInputValue('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleRunBacktest = (strategyVersionId: string, code: string) => {
    if (onRunBacktest) {
      onRunBacktest(strategyVersionId, code);
    }
  };

  return (
    <div className="chat-panel">
      <Card
        title={
          <Space>
            <span>{conversation.title}</span>
            {conversation.tags.map((tag) => (
              <Tag key={tag} color="blue">
                {tag}
              </Tag>
            ))}
          </Space>
        }
        extra={
          <Button icon={<ReloadOutlined />} onClick={onRefresh}>
            刷新
          </Button>
        }
        style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ flex: 1, overflow: 'auto', padding: '16px' }}
      >
        <Spin spinning={loading}>
          <List
            className="message-list"
            dataSource={messages}
            renderItem={(message) => (
              <List.Item
                className={`message-item message-${message.role}`}
                style={{ border: 'none', padding: '8px 0' }}
              >
                <Space align="start" style={{ width: '100%' }}>
                  <Avatar
                    icon={message.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                    style={{
                      backgroundColor: message.role === 'user' ? '#1890ff' : '#52c41a',
                    }}
                  />
                  <div className="message-content" style={{ flex: 1 }}>
                    <div className="message-header">
                      <span className="message-role">
                        {message.role === 'user' ? '我' : 'AI 助手'}
                      </span>
                      <span className="message-time">
                        {new Date(message.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="message-text" style={{ whiteSpace: 'pre-wrap' }}>
                      {message.content}
                    </div>
                    {message.generated_code && (
                      <Card
                        size="small"
                        title="生成的代码"
                        className="code-card"
                        style={{ marginTop: '8px' }}
                        extra={
                          message.strategy_version_id && onRunBacktest && (
                            <Button
                              type="primary"
                              size="small"
                              icon={<ThunderboltOutlined />}
                              onClick={() => handleRunBacktest(message.strategy_version_id!, message.generated_code!)}
                            >
                              运行回测
                            </Button>
                          )
                        }
                      >
                        <pre style={{ margin: 0, overflow: 'auto' }}>
                          <code>{message.generated_code}</code>
                        </pre>
                      </Card>
                    )}
                  </div>
                </Space>
              </List.Item>
            )}
          />
          <div ref={messagesEndRef} />
        </Spin>

        <div className="message-input" style={{ marginTop: '16px' }}>
          <Input.TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入消息... (Shift+Enter 换行，Enter 发送)"
            autoSize={{ minRows: 2, maxRows: 6 }}
            style={{ marginBottom: '8px' }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            disabled={!inputValue.trim()}
            block
          >
            发送
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default ChatPanel;
