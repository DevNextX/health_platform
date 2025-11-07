/**
 * Bind Email Page Component
 * For new WeChat users to bind their email and optionally set password
 */
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, message, Space } from 'antd';
import { UserOutlined, MailOutlined, LockOutlined } from '@ant-design/icons';
import { authAPI } from '../services/api';
import { setTokens } from '../utils/auth';
import { useTranslation } from 'react-i18next';

const { Title, Text } = Typography;

const BindEmail = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();
  
  // Get state from navigation (passed from WeChat callback)
  const wechatState = location.state?.wechatState;

  // If no state, redirect to login
  React.useEffect(() => {
    if (!wechatState) {
      message.warning(t('wechat.no_state') || 'Invalid access, please login again');
      navigate('/login');
    }
  }, [wechatState, navigate, t]);

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const bindData = {
        state: wechatState,
        username: values.username,
        email: values.email,
        password: values.password || undefined, // Optional
        age: values.age,
        gender: values.gender,
        weight: values.weight,
        height: values.height,
      };

      const response = await authAPI.wechatBind(bindData);
      const { access_token, refresh_token } = response.data;
      
      setTokens(access_token, refresh_token);
      message.success(t('wechat.bind_success') || 'Account created successfully');
      navigate('/dashboard');
    } catch (error) {
      console.error('Bind email error:', error);
      const errorMessage = error.response?.data?.message || t('wechat.bind_failed') || 'Failed to bind account';
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <Card style={{ maxWidth: 500, width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ color: '#1890ff', marginBottom: 8 }}>
            {t('wechat.bind_title') || 'Complete Your Profile'}
          </Title>
          <Text type="secondary">
            {t('wechat.bind_subtitle') || 'Please bind your email to continue'}
          </Text>
        </div>

        <Form
          name="bind_email"
          onFinish={onFinish}
          size="large"
          layout="vertical"
        >
          <Form.Item
            name="username"
            label={t('register.username') || 'Username'}
            rules={[
              { required: true, message: t('register.username') + '!' },
              { min: 2, message: t('register.username_min') || 'Username must be at least 2 characters' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder={t('register.username')}
              data-testid="bind-username"
            />
          </Form.Item>

          <Form.Item
            name="email"
            label={t('register.email') || 'Email'}
            rules={[
              { required: true, message: t('register.email') + '!' },
              { type: 'email', message: t('register.email_invalid') || 'Please enter a valid email' }
            ]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder={t('register.email')}
              data-testid="bind-email"
            />
          </Form.Item>

          <Form.Item
            name="password"
            label={
              <span>
                {t('register.password') || 'Password'}{' '}
                <Text type="secondary" style={{ fontSize: 12 }}>
                  ({t('wechat.password_optional') || 'Optional'})
                </Text>
              </span>
            }
            rules={[
              { min: 6, message: t('register.password_min') || 'Password must be at least 6 characters' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder={t('wechat.password_hint') || 'Set password (optional, for email login)'}
              data-testid="bind-password"
            />
          </Form.Item>

          <Form.Item
            name="confirm"
            label={t('register.confirm') || 'Confirm Password'}
            dependencies={['password']}
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value) {
                  const password = getFieldValue('password');
                  // If password is set, confirm must match
                  if (password && (!value || password !== value)) {
                    return Promise.reject(new Error(t('register.password_mismatch') || 'Passwords do not match'));
                  }
                  return Promise.resolve();
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder={t('register.confirm')}
              data-testid="bind-confirm"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              data-testid="bind-submit"
            >
              {t('wechat.bind_button') || 'Complete Registration'}
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {t('wechat.bind_note') || 'Note: If you do not set a password, you can only login via WeChat'}
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default BindEmail;
