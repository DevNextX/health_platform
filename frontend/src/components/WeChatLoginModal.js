/**
 * WeChat Login Modal Component
 * Displays QR code for WeChat login
 */
import React, { useState, useEffect } from 'react';
import { Modal, Spin, message, Typography, Result } from 'antd';
import { WechatOutlined, LoadingOutlined } from '@ant-design/icons';
import { authAPI } from '../services/api';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

const WeChatLoginModal = ({ visible, onCancel, onSuccess }) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [qrcodeUrl, setQrcodeUrl] = useState('');
  const [state, setState] = useState('');
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (visible) {
      loadQRCode();
    } else {
      // Reset state when modal closes
      setQrcodeUrl('');
      setState('');
      setPolling(false);
      setError('');
    }
  }, [visible]);

  const loadQRCode = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await authAPI.wechatLogin();
      const { qrcode_url, state: newState } = response.data;
      setQrcodeUrl(qrcode_url);
      setState(newState);
      
      // Note: In production, actual WeChat login requires opening the URL
      // For testing/demo, we display the URL and instructions
      message.info(t('wechat.qrcode_ready') || 'Please scan QR code with WeChat');
    } catch (err) {
      console.error('Failed to load WeChat QR code:', err);
      setError(t('wechat.load_qr_failed') || 'Failed to load QR code');
      message.error(t('wechat.load_qr_failed') || 'Failed to load QR code');
    } finally {
      setLoading(false);
    }
  };

  const handleManualCallback = async (code) => {
    // This is for testing/demo purposes
    // In production, WeChat will redirect to callback URL automatically
    try {
      const response = await authAPI.wechatCallback({ code, state });
      const data = response.data;
      
      if (data.status === 'existing_user') {
        // User exists, log them in
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        message.success(t('wechat.login_success') || 'Login successful');
        onSuccess({ needBind: false });
      } else if (data.status === 'new_user') {
        // New user, need to bind email
        onSuccess({ needBind: true, state: data.state });
      }
    } catch (err) {
      console.error('WeChat callback error:', err);
      message.error(err.response?.data?.message || t('wechat.callback_failed') || 'Login failed');
    }
  };

  return (
    <Modal
      title={
        <span>
          <WechatOutlined style={{ color: '#09BB07', marginRight: 8 }} />
          {t('wechat.title') || 'WeChat Login'}
        </span>
      }
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={400}
      centered
    >
      <div style={{ textAlign: 'center', padding: '20px 0' }}>
        {loading ? (
          <Spin indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />} />
        ) : error ? (
          <Result
            status="error"
            title={error}
            subTitle={t('wechat.retry_hint') || 'Please try again'}
          />
        ) : qrcodeUrl ? (
          <div>
            <div
              style={{
                border: '2px solid #09BB07',
                borderRadius: 8,
                padding: 20,
                margin: '0 auto 20px',
                maxWidth: 280,
                backgroundColor: '#f5f5f5'
              }}
            >
              <WechatOutlined style={{ fontSize: 120, color: '#09BB07' }} />
            </div>
            <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
              {t('wechat.scan_hint') || 'Please scan QR code with WeChat'}
            </Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {t('wechat.dev_note') || 'Note: This is a development placeholder. In production, a real WeChat QR code will be displayed here.'}
            </Text>
            
            {/* For testing/demo: show the URL */}
            {process.env.NODE_ENV === 'development' && (
              <div style={{ marginTop: 20, padding: 10, background: '#fafafa', borderRadius: 4, fontSize: 12 }}>
                <Text type="secondary">Dev Info:</Text>
                <div style={{ wordBreak: 'break-all', marginTop: 5 }}>
                  <a href={qrcodeUrl} target="_blank" rel="noopener noreferrer">
                    {qrcodeUrl}
                  </a>
                </div>
                <Text type="secondary" style={{ display: 'block', marginTop: 10 }}>
                  State: {state}
                </Text>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </Modal>
  );
};

export default WeChatLoginModal;
