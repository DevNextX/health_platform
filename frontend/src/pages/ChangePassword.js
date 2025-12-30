import React, { useMemo, useState } from 'react';
import { Card, Form, Input, Button, Typography, message, Progress, Row, Col } from 'antd';
import { authAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import FirstLoginGuide from '../components/FirstLoginGuide';
import { useTranslation } from 'react-i18next';

const { Title, Text } = Typography;

const ChangePassword = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { t } = useTranslation();

  const onFinish = async (values) => {
    const { current_password, new_password, confirm_password } = values;
    if (new_password !== confirm_password) {
      message.error(t('settings.password.mismatch'));
      return;
    }
    setLoading(true);
    try {
      await authAPI.changePassword({ current_password, new_password });
      message.success(t('settings.password.relogin') || t('settings.password.changed'));
      try { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); } catch {}
      navigate('/login');
    } catch (e) {
      const msg = e.response?.data?.message || t('settings.password.failed');
      message.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const strength = useMemo(() => {
    // simple strength meter: length + variety
    return (pwd) => {
      if (!pwd) return 0;
      let score = 0;
      if (pwd.length >= 8) score += 30;
      if (/[a-z]/.test(pwd)) score += 20;
      if (/[A-Z]/.test(pwd)) score += 20;
      if (/[0-9]/.test(pwd)) score += 20;
      if (/[^A-Za-z0-9]/.test(pwd)) score += 10;
      return Math.min(score, 100);
    };
  }, []);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <Card style={{ width: 640 }}>
        <Title level={3} style={{ textAlign: 'center', marginBottom: 8 }}>{t('firstLogin.title')}</Title>
        <FirstLoginGuide />
        <Row gutter={24}>
          <Col xs={24} md={14}>
            <Form layout="vertical" onFinish={onFinish}>
              <Form.Item label={t('settings.password.current')} name="current_password" rules={[{ required: true, message: t('settings.password.currentReq') }]}>
                <Input.Password placeholder={t('settings.password.current')} autoFocus />
              </Form.Item>
              <Form.Item label={t('settings.password.new')} name="new_password" rules={[{ required: true, message: t('settings.password.newReq') }]}>
                <Input.Password placeholder={t('settings.password.new')} onChange={(e) => (window.__pwd = e.target.value)} />
              </Form.Item>
              <Form.Item label={t('settings.password.confirm')} name="confirm_password" rules={[{ required: true, message: t('settings.password.confirmReq') }]}>
                <Input.Password placeholder={t('settings.password.confirm')} />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>{t('settings.password.submit')}</Button>
              </Form.Item>
            </Form>
          </Col>
          <Col xs={24} md={10}>
            <div style={{ paddingTop: 8 }}>
              <Text type="secondary">{t('settings.password.strength')}</Text>
              <Progress percent={strength(window.__pwd || '')} showInfo={false} status="active" style={{ marginTop: 6 }} />
              <div style={{ marginTop: 8 }}>
                <ul style={{ paddingLeft: 18, margin: 0 }}>
                  <li>{t('settings.password.ruleLen')}</li>
                  <li>{t('settings.password.ruleMix')}</li>
                  <li>{t('settings.password.ruleAdv')}</li>
                </ul>
              </div>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default ChangePassword;
