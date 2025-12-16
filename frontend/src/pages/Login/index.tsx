/**
 * 登录页面
 */
import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Tabs, message, Space } from 'antd';
import { UserOutlined, LockOutlined, MobileOutlined, SafetyOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/services/auth';
import './index.css';

const { TabPane } = Tabs;

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, isLoading, error, clearError } = useAuthStore();

  const [form] = Form.useForm();
  const [loginType, setLoginType] = useState<'password' | 'code'>('password');
  const [countdown, setCountdown] = useState(0);
  const [sending, setSending] = useState(false);

  // 如果已登录，跳转到首页
  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as any)?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  // 显示错误消息
  useEffect(() => {
    if (error) {
      message.error(error);
      clearError();
    }
  }, [error, clearError]);

  // 验证码倒计时
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  /**
   * 发送验证码
   */
  const handleSendCode = async () => {
    try {
      const phone = form.getFieldValue('phone');
      if (!phone) {
        message.warning('请输入手机号');
        return;
      }

      // 验证手机号格式
      const phoneRegex = /^1[3-9]\d{9}$/;
      if (!phoneRegex.test(phone)) {
        message.warning('请输入正确的手机号');
        return;
      }

      setSending(true);
      const response = await authApi.sendCode({
        phone,
        purpose: 'login',
      });

      message.success(response.message);
      setCountdown(60);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '发送验证码失败');
    } finally {
      setSending(false);
    }
  };

  /**
   * 处理登录
   */
  const handleLogin = async (values: any) => {
    try {
      if (loginType === 'password') {
        await login({
          phone: values.phone,
          password: values.password,
        });
      } else {
        await login({
          phone: values.phone_code,
          verification_code: values.code,
        });
      }
      message.success('登录成功');
    } catch (error: any) {
      // 错误已在 store 中处理
      console.error('Login error:', error);
    }
  };

  /**
   * 跳转到注册页面
   */
  const handleGoToRegister = () => {
    navigate('/register');
  };

  return (
    <div className="login-container">
      <Card
        className="login-card"
        title={
          <div className="login-header">
            <h2>量化投资平台</h2>
            <p>登录您的账户</p>
          </div>
        }
      >
        <Tabs activeKey={loginType} onChange={(key) => setLoginType(key as any)}>
          <TabPane tab="密码登录" key="password">
            <Form
              form={form}
              name="password-login"
              onFinish={handleLogin}
              autoComplete="off"
              size="large"
            >
              <Form.Item
                name="phone"
                rules={[
                  { required: true, message: '请输入手机号' },
                  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
                ]}
              >
                <Input
                  prefix={<MobileOutlined />}
                  placeholder="手机号"
                  maxLength={11}
                />
              </Form.Item>

              <Form.Item
                name="password"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 6, message: '密码至少6位' },
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="密码"
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={isLoading}
                  block
                >
                  登录
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab="验证码登录" key="code">
            <Form
              form={form}
              name="code-login"
              onFinish={handleLogin}
              autoComplete="off"
              size="large"
            >
              <Form.Item
                name="phone_code"
                rules={[
                  { required: true, message: '请输入手机号' },
                  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
                ]}
              >
                <Input
                  prefix={<MobileOutlined />}
                  placeholder="手机号"
                  maxLength={11}
                />
              </Form.Item>

              <Form.Item
                name="code"
                rules={[
                  { required: true, message: '请输入验证码' },
                  { len: 6, message: '请输入6位验证码' },
                ]}
              >
                <Space.Compact style={{ width: '100%' }}>
                  <Input
                    prefix={<SafetyOutlined />}
                    placeholder="验证码"
                    maxLength={6}
                  />
                  <Button
                    onClick={handleSendCode}
                    loading={sending}
                    disabled={countdown > 0}
                  >
                    {countdown > 0 ? `${countdown}秒后重试` : '获取验证码'}
                  </Button>
                </Space.Compact>
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={isLoading}
                  block
                >
                  登录
                </Button>
              </Form.Item>
            </Form>
          </TabPane>
        </Tabs>

        <div className="login-footer">
          <Button type="link" onClick={handleGoToRegister}>
            还没有账号？立即注册
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;
