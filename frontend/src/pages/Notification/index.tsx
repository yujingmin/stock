/**
 * 通知中心页面
 * 显示系统通知、策略信号、风控预警等
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Tag,
  Button,
  Space,
  Badge,
  Tabs,
  message,
  Modal,
  Dropdown,
  Menu,
  Empty,
  Spin,
  DatePicker,
  Select,
} from 'antd';
import {
  BellOutlined,
  CheckOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  FilterOutlined,
  ReloadOutlined,
  WarningOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import './index.css';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const { TabPane } = Tabs;
const { RangePicker } = DatePicker;
const { Option } = Select;

// 通知类型枚举
enum NotificationType {
  RISK_ALERT = 'risk_alert',
  STRATEGY_SIGNAL = 'strategy_signal',
  POSITION_REMINDER = 'position_reminder',
  SYSTEM_NOTICE = 'system_notice',
  DATA_ANOMALY = 'data_anomaly',
  BACKTEST_COMPLETE = 'backtest_complete',
}

// 优先级枚举
enum NotificationPriority {
  URGENT = 'urgent',
  NORMAL = 'normal',
  MINOR = 'minor',
}

interface Notification {
  notification_id: string;
  type: NotificationType;
  priority: NotificationPriority;
  title: string;
  content: string;
  target_symbol?: string;
  strategy_id?: string;
  task_id?: string;
  trigger_condition?: string;
  trigger_value?: number;
  extra_data?: Record<string, any>;
  read_status: boolean;
  pushed: boolean;
  push_channel?: string;
  follow_up: boolean;
  follow_up_time?: string;
  created_at: string;
  updated_at: string;
  read_at?: string;
  pushed_at?: string;
}

const NotificationCenter: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [activeTab, setActiveTab] = useState('all');
  const [filterType, setFilterType] = useState<NotificationType | undefined>();
  const [filterPriority, setFilterPriority] = useState<NotificationPriority | undefined>();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // 加载通知列表
  const loadNotifications = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('limit', pageSize.toString());
      params.append('offset', ((page - 1) * pageSize).toString());

      if (filterType) {
        params.append('type', filterType);
      }
      if (filterPriority) {
        params.append('priority', filterPriority);
      }
      if (activeTab === 'unread') {
        params.append('read_status', 'false');
      } else if (activeTab === 'follow_up') {
        params.append('follow_up', 'true');
      }

      const response = await fetch(`/api/v1/notification/?${params.toString()}`);
      if (!response.ok) {
        throw new Error('加载通知失败');
      }

      const data = await response.json();
      setNotifications(data.notifications);
      setTotal(data.total);
      setUnreadCount(data.unread_count);
    } catch (error: any) {
      message.error(error.message || '加载通知失败');
    } finally {
      setLoading(false);
    }
  };

  // 标记为已读
  const markAsRead = async (notificationId: string) => {
    try {
      const response = await fetch(`/api/v1/notification/${notificationId}/read`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('标记已读失败');
      }

      message.success('已标记为已读');
      loadNotifications();
    } catch (error: any) {
      message.error(error.message || '操作失败');
    }
  };

  // 全部标记为已读
  const markAllAsRead = async () => {
    try {
      const response = await fetch('/api/v1/notification/read-all', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('操作失败');
      }

      const data = await response.json();
      message.success(data.message);
      loadNotifications();
    } catch (error: any) {
      message.error(error.message || '操作失败');
    }
  };

  // 删除通知
  const deleteNotification = async (notificationId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条通知吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await fetch(`/api/v1/notification/${notificationId}`, {
            method: 'DELETE',
          });

          if (!response.ok) {
            throw new Error('删除失败');
          }

          message.success('删除成功');
          loadNotifications();
        } catch (error: any) {
          message.error(error.message || '删除失败');
        }
      },
    });
  };

  // 查看通知详情
  const viewNotificationDetail = (notification: Notification) => {
    Modal.info({
      title: notification.title,
      width: 600,
      content: (
        <div style={{ marginTop: 16 }}>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 14 }}>
            {notification.content}
          </pre>
          {notification.target_symbol && (
            <p style={{ marginTop: 12 }}>
              <strong>关联股票：</strong>{notification.target_symbol}
            </p>
          )}
          {notification.trigger_condition && (
            <p>
              <strong>触发条件：</strong>{notification.trigger_condition}
            </p>
          )}
          {notification.trigger_value !== undefined && (
            <p>
              <strong>触发值：</strong>{notification.trigger_value}
            </p>
          )}
          <p style={{ color: '#999', fontSize: 12, marginTop: 12 }}>
            {dayjs(notification.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </p>
        </div>
      ),
      onOk: () => {
        if (!notification.read_status) {
          markAsRead(notification.notification_id);
        }
      },
    });
  };

  // 获取类型标签
  const getTypeTag = (type: NotificationType) => {
    const typeMap: Record<NotificationType, { color: string; text: string; icon: any }> = {
      [NotificationType.RISK_ALERT]: {
        color: 'red',
        text: '风控预警',
        icon: <WarningOutlined />,
      },
      [NotificationType.STRATEGY_SIGNAL]: {
        color: 'blue',
        text: '策略信号',
        icon: <BellOutlined />,
      },
      [NotificationType.BACKTEST_COMPLETE]: {
        color: 'green',
        text: '回测完成',
        icon: <CheckOutlined />,
      },
      [NotificationType.DATA_ANOMALY]: {
        color: 'orange',
        text: '数据异常',
        icon: <ExclamationCircleOutlined />,
      },
      [NotificationType.SYSTEM_NOTICE]: {
        color: 'default',
        text: '系统通知',
        icon: <InfoCircleOutlined />,
      },
      [NotificationType.POSITION_REMINDER]: {
        color: 'purple',
        text: '持仓提醒',
        icon: <BellOutlined />,
      },
    };
    const config = typeMap[type] || typeMap[NotificationType.SYSTEM_NOTICE];
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  // 获取优先级标签
  const getPriorityTag = (priority: NotificationPriority) => {
    const priorityMap: Record<NotificationPriority, { color: string; text: string }> = {
      [NotificationPriority.URGENT]: { color: 'red', text: '紧急' },
      [NotificationPriority.NORMAL]: { color: 'blue', text: '普通' },
      [NotificationPriority.MINOR]: { color: 'default', text: '次要' },
    };
    const config = priorityMap[priority];
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 初始加载
  useEffect(() => {
    loadNotifications();
  }, [activeTab, filterType, filterPriority, page]);

  return (
    <div className="notification-center">
      <Card
        title={
          <Space>
            <BellOutlined />
            通知中心
            {unreadCount > 0 && <Badge count={unreadCount} />}
          </Space>
        }
        extra={
          <Space>
            <Select
              placeholder="类型筛选"
              allowClear
              style={{ width: 120 }}
              onChange={(value) => setFilterType(value)}
              value={filterType}
            >
              <Option value={NotificationType.RISK_ALERT}>风控预警</Option>
              <Option value={NotificationType.STRATEGY_SIGNAL}>策略信号</Option>
              <Option value={NotificationType.BACKTEST_COMPLETE}>回测完成</Option>
              <Option value={NotificationType.DATA_ANOMALY}>数据异常</Option>
            </Select>
            <Select
              placeholder="优先级筛选"
              allowClear
              style={{ width: 100 }}
              onChange={(value) => setFilterPriority(value)}
              value={filterPriority}
            >
              <Option value={NotificationPriority.URGENT}>紧急</Option>
              <Option value={NotificationPriority.NORMAL}>普通</Option>
              <Option value={NotificationPriority.MINOR}>次要</Option>
            </Select>
            <Button icon={<ReloadOutlined />} onClick={loadNotifications}>
              刷新
            </Button>
            {unreadCount > 0 && (
              <Button type="primary" onClick={markAllAsRead}>
                全部已读
              </Button>
            )}
          </Space>
        }
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="全部通知" key="all" />
          <TabPane
            tab={
              <Badge count={unreadCount} offset={[10, 0]}>
                未读通知
              </Badge>
            }
            key="unread"
          />
          <TabPane tab="需要跟进" key="follow_up" />
        </Tabs>

        <Spin spinning={loading}>
          {notifications.length > 0 ? (
            <List
              itemLayout="horizontal"
              dataSource={notifications}
              pagination={{
                current: page,
                pageSize: pageSize,
                total: total,
                onChange: (newPage) => setPage(newPage),
                showSizeChanger: false,
                showTotal: (total) => `共 ${total} 条通知`,
              }}
              renderItem={(item) => (
                <List.Item
                  className={`notification-item ${!item.read_status ? 'unread' : ''}`}
                  actions={[
                    !item.read_status && (
                      <Button
                        type="link"
                        size="small"
                        icon={<CheckOutlined />}
                        onClick={() => markAsRead(item.notification_id)}
                      >
                        标记已读
                      </Button>
                    ),
                    <Button
                      type="link"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => deleteNotification(item.notification_id)}
                    >
                      删除
                    </Button>,
                  ]}
                  onClick={() => viewNotificationDetail(item)}
                  style={{ cursor: 'pointer' }}
                >
                  <List.Item.Meta
                    avatar={
                      !item.read_status && (
                        <Badge dot status="processing" />
                      )
                    }
                    title={
                      <Space>
                        {getTypeTag(item.type)}
                        {getPriorityTag(item.priority)}
                        <span>{item.title}</span>
                        {item.target_symbol && (
                          <Tag color="cyan">{item.target_symbol}</Tag>
                        )}
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={4}>
                        <div
                          style={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            maxWidth: 800,
                          }}
                        >
                          {item.content}
                        </div>
                        <span style={{ color: '#999', fontSize: 12 }}>
                          {dayjs(item.created_at).fromNow()}
                        </span>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          ) : (
            <Empty description="暂无通知" />
          )}
        </Spin>
      </Card>
    </div>
  );
};

export default NotificationCenter;
