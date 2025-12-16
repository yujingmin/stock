/**
 * 注册页面
 */
import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, message, Space, Checkbox } from 'antd';
import { UserOutlined, LockOutlined, MobileOutlined, SafetyOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/services/auth';
import './index.css';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register, isAuthenticated, isLoading, error, clearError } = useAuthStore();

  const [form] = Form.useForm();
  const [countdown, setCountdown] = useState(0);
  const [sending, setSending] = useState(false);
  const [agreed, setAgreed] = useState(false);

  // 如果已登录，跳转到首页
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

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
        purpose: 'register',
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
   * 处理注册
   */
  const handleRegister = async (values: any) => {
    if (!agreed) {
      message.warning('请先阅读并同意用户协议和隐私政策');
      return;
    }

    try {
      await register({
        username: values.username,
        phone: values.phone,
        password: values.password,
        verification_code: values.code,
      });
      message.success('注册成功');
      // 注册成功后自动跳转到首页
    } catch (error: any) {
      // 错误已在 store 中处理
      console.error('Register error:', error);
    }
  };

  /**
   * 跳转到登录页面
   */
  const handleGoToLogin = () => {
    navigate('/login');
  };

  return (
    <div className="register-container">
      <Card
        className="register-card"
        title={
          <div className="register-header">
            <h2>量化投资平台</h2>
            <p>创建您的账户</p>
          </div>
        }
      >
        <Form
          form={form}
          name="register"
          onFinish={handleRegister}
          autoComplete="off"
          size="large"
          layout="vertical"
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, max: 50, message: '用户名长度3-50位' },
              {
                pattern: /^[a-zA-Z0-9_]+$/,
                message: '用户名只能包含字母、数字和下划线',
              },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="请输入用户名"
            />
          </Form.Item>

          <Form.Item
            name="phone"
            label="手机号"
            rules={[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
            ]}
          >
            <Input
              prefix={<MobileOutlined />}
              placeholder="请输入手机号"
              maxLength={11}
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, max: 50, message: '密码长度6-50位' },
            ]}
            hasFeedback
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入密码"
            />
          </Form.Item>

          <Form.Item
            name="confirm"
            label="确认密码"
            dependencies={['password']}
            hasFeedback
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请再次输入密码"
            />
          </Form.Item>

          <Form.Item
            name="code"
            label="验证码"
            rules={[
              { required: true, message: '请输入验证码' },
              { len: 6, message: '请输入6位验证码' },
            ]}
          >
            <Space.Compact style={{ width: '100%' }}>
              <Input
                prefix={<SafetyOutlined />}
                placeholder="请输入验证码"
                maxLength={6}
              />
              <Button
                onClick={handleSendCode}
                loading={sending}
                disabled={countdown > 0}
                style={{ width: '140px' }}
              >
                {countdown > 0 ? `${countdown}秒后重试` : '获取验证码'}
              </Button>
            </Space.Compact>
          </Form.Item>

          <Form.Item>
            <Checkbox checked={agreed} onChange={(e) => setAgreed(e.target.checked)}>
              我已阅读并同意
              <Button type="link" size="small">用户协议</Button>
              和
              <Button type="link" size="small">隐私政策</Button>
            </Checkbox>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={isLoading}
              block
            >
              注册
            </Button>
          </Form.Item>
        </Form>

        <div className="register-footer">
          <Button type="link" onClick={handleGoToLogin}>
            已有账号？立即登录
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default RegisterPage;
