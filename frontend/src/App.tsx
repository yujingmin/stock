import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  LineChartOutlined,
  FundOutlined,
  DashboardOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

import MarketDataPage from './pages/MarketData';
import BacktestingPage from './pages/Backtesting';
import './App.css';

const { Header, Content, Sider } = Layout;

const App: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

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
      disabled: true,
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

  return (
    <Layout className="app" style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
          量化投资平台
        </div>
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
              <Route path="/market-data" element={<MarketDataPage />} />
              <Route path="/backtesting" element={<BacktestingPage />} />
              <Route path="/login" element={<div>登录页面（待实现）</div>} />
              <Route path="*" element={<Navigate to="/market-data" replace />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default App;
