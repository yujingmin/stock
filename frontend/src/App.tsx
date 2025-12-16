import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Menu, Dropdown, Avatar, Space } from 'antd';
import {
  LineChartOutlined,
  FundOutlined,
  DashboardOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { ProtectedRoute, GuestRoute } from './components/ProtectedRoute';

import MarketDataPage from './pages/MarketData';
import BacktestingPage from './pages/Backtesting';
import StrategyPage from './pages/Strategy';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';
import './App.css';

const { Header, Content, Sider } = Layout;

const App: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, logout, fetchCurrentUser } = useAuthStore();

  // 应用启动时尝试恢复登录状态
  useEffect(() => {
    if (!isAuthenticated) {
      fetchCurrentUser();
    }
  }, []);

  // 处理登出
  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // 用户下拉菜单
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  const menuItems = [
    {
      key: '/market-data',
      icon: <LineChartOutlined />,
      label: '市场数据',
    },
    {
      key: '/strategy',
      icon: <FundOutlined />,
      label: '策略开发',
      disabled: false,  // 启用策略开发
    },
    {
      key: '/backtesting',
      icon: <DashboardOutlined />,
      label: '回测系统',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
      disabled: true,
    },
  ];

  // 不需要布局的路由（登录、注册页）
  const isAuthRoute = location.pathname === '/login' || location.pathname === '/register';

  if (isAuthRoute) {
    return (
      <Routes>
        <Route
          path="/login"
          element={
            <GuestRoute>
              <LoginPage />
            </GuestRoute>
          }
        />
        <Route
          path="/register"
          element={
            <GuestRoute>
              <RegisterPage />
            </GuestRoute>
          }
        />
      </Routes>
    );
  }

  return (
    <Layout className="app" style={{ minHeight: '100vh' }}>
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px'
      }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
          量化投资平台
        </div>

        {isAuthenticated && user && (
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} src={user.avatar_url} />
              <span style={{ color: 'white' }}>
                {user.nickname || user.username}
              </span>
            </Space>
          </Dropdown>
        )}
      </Header>

      <Layout>
        <Sider width={200} theme="light">
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
          />
        </Sider>
        <Layout style={{ padding: '0 24px 24px' }}>
          <Content>
            <Routes>
              <Route path="/" element={<Navigate to="/market-data" replace />} />
              <Route
                path="/market-data"
                element={
                  <ProtectedRoute>
                    <MarketDataPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/strategy"
                element={
                  <ProtectedRoute>
                    <StrategyPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/backtesting"
                element={
                  <ProtectedRoute>
                    <BacktestingPage />
                  </ProtectedRoute>
                }
              />
              <Route path="*" element={<Navigate to="/market-data" replace />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default App;
