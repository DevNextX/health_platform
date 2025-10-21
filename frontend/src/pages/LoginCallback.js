/**
 * GitHub OAuth Callback Handler
 * Handles the redirect from GitHub OAuth and stores tokens
 */
import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Spin, message } from 'antd';
import { setTokens } from '../utils/auth';
import { useTranslation } from 'react-i18next';

const LoginCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { t } = useTranslation();

  useEffect(() => {
    const accessToken = searchParams.get('access_token');
    const refreshToken = searchParams.get('refresh_token');
    const error = searchParams.get('error');

    if (error) {
      let errorMessage = t('messages.login.fail');
      
      if (error === 'github_cancelled') {
        errorMessage = t('messages.github.cancelled') || 'GitHub login cancelled';
      } else if (error === 'github_failed') {
        errorMessage = t('messages.github.failed') || 'GitHub login failed. Please try again.';
      } else if (error === 'email_exists') {
        errorMessage = t('messages.github.emailExists') || 'Email already registered';
      }
      
      message.error(errorMessage);
      navigate('/login');
      return;
    }

    if (accessToken && refreshToken) {
      setTokens(accessToken, refreshToken);
      message.success(t('messages.login.success'));
      navigate('/dashboard');
    } else {
      message.error(t('messages.login.fail'));
      navigate('/login');
    }
  }, [searchParams, navigate, t]);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }}>
      <Spin size="large" />
    </div>
  );
};

export default LoginCallback;
