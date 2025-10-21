/**
 * Complete GitHub Registration Page
 * For users whose GitHub email is private
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, message } from 'antd';
import { MailOutlined } from '@ant-design/icons';
import { setTokens } from '../utils/auth';
import { useTranslation } from 'react-i18next';
import api from '../services/api';

const { Title, Text, Paragraph } = Typography;

const CompleteRegistration = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const response = await api.post('/api/v1/auth/github/complete', {
        email: values.email
      });
      
      const { access_token, refresh_token } = response.data;
      setTokens(access_token, refresh_token);
      message.success(t('messages.registration.success') || 'Registration completed successfully');
      navigate('/dashboard');
    } catch (error) {
      console.error('Complete registration error:', error);
      const errorMessage = error.response?.data?.message || 
                          t('messages.registration.fail') || 
                          'Failed to complete registration';
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
            {t('completeRegistration.title') || 'Complete Your Registration'}
          </Title>
          <Paragraph type="secondary">
            {t('completeRegistration.subtitle') || 
             'Your GitHub email is private. Please provide an email address to complete your registration.'}
          </Paragraph>
        </div>

        <Form
          name="complete-registration"
          onFinish={onFinish}
          size="large"
          layout="vertical"
        >
          <Form.Item
            label={t('register.email') || 'Email'}
            name="email"
            rules={[
              { 
                required: true, 
                message: t('completeRegistration.emailRequired') || 'Please enter your email address' 
              },
              { 
                type: 'email', 
                message: t('completeRegistration.emailInvalid') || 'Please enter a valid email address' 
              }
            ]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder={t('completeRegistration.emailPlaceholder') || 'Enter your email'}
              data-testid="complete-email"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              data-testid="complete-submit"
            >
              {t('completeRegistration.submit') || 'Complete Registration'}
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Button 
            type="link" 
            onClick={() => navigate('/login')}
          >
            {t('completeRegistration.backToLogin') || 'Back to Login'}
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default CompleteRegistration;
